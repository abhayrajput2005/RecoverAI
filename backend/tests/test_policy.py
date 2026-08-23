from app.classifier import classify_failure
from app.models import RecoveryAction
from app.policy import authorize, decide_action
from app.rules import HIGH_VALUE_THRESHOLD_INR


def test_adversarial_case_always_do_not_retry():
    classification = classify_failure("CARD_REPORTED_LOST", "lost card", 0)
    decision = decide_action("RC-1", classification, recovery_score=0.9, amount=500, retry_count=0)
    assert decision.recommended_action == RecoveryAction.do_not_retry
    assert decision.is_terminal is True


def test_retry_cap_forces_do_not_retry_even_with_high_score():
    classification = classify_failure("INSUFFICIENT_FUNDS", "no funds", 3)
    decision = decide_action("RC-2", classification, recovery_score=0.95, amount=500, retry_count=3)
    assert decision.recommended_action == RecoveryAction.do_not_retry


def test_high_value_case_escalates_regardless_of_score():
    classification = classify_failure("CARD_EXPIRED", "expired", 0)
    decision = decide_action(
        "RC-3", classification, recovery_score=0.95, amount=HIGH_VALUE_THRESHOLD_INR + 1, retry_count=0
    )
    assert decision.recommended_action == RecoveryAction.escalate_human_review


def test_high_score_clear_case_gets_immediate_retry():
    classification = classify_failure("CARD_EXPIRED", "expired", 0)
    decision = decide_action("RC-4", classification, recovery_score=0.8, amount=500, retry_count=0)
    assert decision.recommended_action == RecoveryAction.immediate_retry


def test_low_score_non_terminal_case_escalates_for_review():
    classification = classify_failure("SOME_NEW_CODE", "weird", 0)
    decision = decide_action("RC-5", classification, recovery_score=0.1, amount=500, retry_count=0)
    assert decision.recommended_action == RecoveryAction.escalate_human_review


def test_authorize_overrides_llm_decision_that_violates_retry_cap():
    from app.models import AgentDecision

    bad_decision = AgentDecision(
        case_id="RC-6",
        recommended_action=RecoveryAction.immediate_retry,  # would violate the cap
        confidence=0.9,
        recovery_probability=0.9,
        reasoning="model was overconfident",
        is_terminal=False,
    )
    fixed = authorize(bad_decision, amount=500, retry_count=3)
    assert fixed.recommended_action == RecoveryAction.do_not_retry
    assert "OVERRIDDEN" in fixed.reasoning


def test_authorize_overrides_llm_decision_above_high_value_threshold():
    from app.models import AgentDecision

    bad_decision = AgentDecision(
        case_id="RC-7",
        recommended_action=RecoveryAction.immediate_retry,
        confidence=0.9,
        recovery_probability=0.9,
        reasoning="model ignored the threshold",
        is_terminal=False,
    )
    fixed = authorize(bad_decision, amount=HIGH_VALUE_THRESHOLD_INR + 500, retry_count=0)
    assert fixed.recommended_action == RecoveryAction.escalate_human_review
    assert "OVERRIDDEN" in fixed.reasoning
