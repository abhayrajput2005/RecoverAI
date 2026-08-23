"""
Tool: create_retry_or_payment_link — Initiate the permitted recovery
workflow via Razorpay (Day 7-8).

Guardrails enforced HERE, independent of whatever authorized the action
upstream (report Section 5 + risk mitigation table):
  - Idempotency: a case that's already action_taken/recovered is never
    re-actioned, no matter how many times this gets called.
  - Cooldown: won't fire a new retry within COOLDOWN_HOURS of the last one.
  - do_not_retry / escalate_human_review never reach the Razorpay API at all
    — those are terminal/manual-only outcomes, not executable actions.
"""

from datetime import timedelta

from app.audit import log_decision
from app.db import CaseRecord, get_session, utcnow
from app.models import RecoveryAction
from app.razorpay_client import create_order, create_payment_link
from app.rules import COOLDOWN_HOURS

# Actions that actually hit the Razorpay API. Anything else is a no-op here.
_EXECUTABLE_ACTIONS = {
    RecoveryAction.immediate_retry,
    RecoveryAction.scheduled_retry,
    RecoveryAction.alternative_method,
    RecoveryAction.payment_link,
}


class IdempotencyError(Exception):
    pass


class CooldownError(Exception):
    pass


def create_retry_or_payment_link(case_id: str, action: RecoveryAction) -> dict:
    if action not in _EXECUTABLE_ACTIONS:
        log_decision(case_id, "execution", {"skipped": True, "reason": f"action '{action.value}' is not executable"})
        return {"executed": False, "reason": f"'{action.value}' does not call Razorpay"}

    session = get_session()
    try:
        case = session.query(CaseRecord).filter_by(case_id=case_id).one_or_none()
        if case is None:
            raise ValueError(f"Unknown case_id: {case_id}")

        # --- Idempotency guardrail ---
        if case.status in ("action_taken", "recovered"):
            log_decision(case_id, "execution", {"blocked": "idempotency", "current_status": case.status})
            raise IdempotencyError(f"Case {case_id} already has status '{case.status}'; refusing to re-action.")

        # --- Cooldown guardrail ---
        if case.last_action_at is not None:
            elapsed = utcnow() - case.last_action_at.replace(tzinfo=utcnow().tzinfo)
            if elapsed < timedelta(hours=COOLDOWN_HOURS):
                log_decision(case_id, "execution", {
                    "blocked": "cooldown",
                    "hours_remaining": round(COOLDOWN_HOURS - elapsed.total_seconds() / 3600, 1),
                })
                raise CooldownError(
                    f"Case {case_id} was actioned {elapsed} ago; cooldown is {COOLDOWN_HOURS}h."
                )

        # --- Execute against Razorpay test mode ---
        if action == RecoveryAction.immediate_retry:
            result = create_order(case.amount, receipt=case_id, notes={"case_id": case_id, "action": action.value})
            reference_id = result["id"]
        else:
            result = create_payment_link(
                case.amount,
                description=f"Complete your payment — {case_id}",
                customer_id=case.customer_id,
                notes={"case_id": case_id, "action": action.value},
            )
            reference_id = result["id"]

        case.status = "action_taken"
        case.last_action = action.value
        case.last_action_at = utcnow()
        case.retry_count = (case.retry_count or 0) + 1
        case.razorpay_reference_id = reference_id
        session.commit()

        log_decision(case_id, "execution", {
            "executed": True, "action": action.value, "razorpay_reference_id": reference_id,
        })
        return {"executed": True, "razorpay_reference_id": reference_id, "raw": result}

    finally:
        session.close()
