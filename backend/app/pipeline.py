"""
Day 9 pipeline — runs the full closed loop (report Section 2: Detect ->
Understand -> Predict -> Decide -> Act) for a single case already sitting
in the DB, and updates its status accordingly:

  - do_not_retry recommendation      -> status = 'do_not_retry', nothing executed
  - escalate_human_review            -> status = 'in_review', nothing executed
                                         (needs POST /cases/{id}/approve)
  - any other action                 -> executed immediately via
                                         create_retry_or_payment_link
"""

from app.audit import log_decision
from app.db import CaseRecord, get_session
from app.models import RecoveryAction
from app.tools.analyze_failure import analyze_failure
from app.tools.calculate_recovery_score import calculate_recovery_score
from app.tools.create_retry_or_payment_link import (
    CooldownError,
    IdempotencyError,
    create_retry_or_payment_link,
)
from app.tools.recommend_action import recommend_action


def process_case(case_id: str) -> dict:
    session = get_session()
    try:
        case = session.query(CaseRecord).filter_by(case_id=case_id).one_or_none()
        if case is None:
            raise ValueError(f"Unknown case_id: {case_id}")

        customer_history = {
            "successful_payments_last_90d": case.successful_payments_last_90d,
            "failed_payments_last_90d": case.failed_payments_last_90d,
            "is_subscription": case.is_subscription,
        }

        classification = analyze_failure(case.failure_code, case.gateway_message, case.retry_count)
        score = calculate_recovery_score(case_id, classification, customer_history, case.retry_count)
        decision = recommend_action(
            case_id=case_id,
            recovery_score=score,
            classification=classification,
            amount=case.amount,
            retry_count=case.retry_count,
            gateway_message=case.gateway_message,
            failure_code=case.failure_code,
            customer_history=customer_history,
        )

        case.classification_bucket = classification["bucket"]

        if decision.recommended_action == RecoveryAction.do_not_retry:
            case.status = "do_not_retry"
            session.commit()
            return {"case_id": case_id, "action": "do_not_retry", "executed": False}

        if decision.recommended_action == RecoveryAction.escalate_human_review:
            case.status = "in_review"
            session.commit()
            return {"case_id": case_id, "action": "escalate_human_review", "executed": False,
                     "note": "awaiting POST /cases/{case_id}/approve"}

        session.commit()  # persist classification_bucket before executing

        try:
            exec_result = create_retry_or_payment_link(case_id, decision.recommended_action)
        except (IdempotencyError, CooldownError) as e:
            log_decision(case_id, "execution", {"blocked": str(e)})
            return {"case_id": case_id, "action": decision.recommended_action.value, "executed": False, "blocked_reason": str(e)}

        return {"case_id": case_id, "action": decision.recommended_action.value, "executed": exec_result["executed"]}

    finally:
        session.close()


def approve_case(case_id: str) -> dict:
    """
    Simulated human-approval step (report Section 5 guardrail: "No action
    above a configurable ₹ threshold without a simulated approval step").
    Only valid for cases currently sitting in 'in_review'. Re-runs the
    scoring/decision with the high-value guardrail bypassed, then executes.
    """
    from app.policy import decide_action

    session = get_session()
    try:
        case = session.query(CaseRecord).filter_by(case_id=case_id).one_or_none()
        if case is None:
            raise ValueError(f"Unknown case_id: {case_id}")
        if case.status != "in_review":
            raise ValueError(f"Case {case_id} is not awaiting review (status='{case.status}')")

        customer_history = {
            "successful_payments_last_90d": case.successful_payments_last_90d,
            "failed_payments_last_90d": case.failed_payments_last_90d,
            "is_subscription": case.is_subscription,
        }
        classification = analyze_failure(case.failure_code, case.gateway_message, case.retry_count)
        score = calculate_recovery_score(case_id, classification, customer_history, case.retry_count)
        decision = decide_action(
            case_id, classification, score, case.amount, case.retry_count,
            bypass_high_value_guardrail=True,
        )
        log_decision(case_id, "policy_override", {"approved": True, **decision.model_dump()})

        if decision.recommended_action in (RecoveryAction.do_not_retry,):
            case.status = "do_not_retry"
            session.commit()
            return {"case_id": case_id, "action": "do_not_retry", "executed": False}

        session.commit()
        exec_result = create_retry_or_payment_link(case_id, decision.recommended_action)
        return {"case_id": case_id, "action": decision.recommended_action.value, "executed": exec_result["executed"]}

    finally:
        session.close()
