"""
Deterministic policy engine (report Section 5 guardrails + Section 2 design
principle: "the model recommends, deterministic application logic
authorizes and executes").

This module is the ONLY place allowed to produce a final, executable
RecoveryAction. From Day 4-6 onward, the LLM's recommend_action() output for
ambiguous cases is still passed through authorize() below before anything
can be executed — the agent proposes, this function disposes.
"""

from app.classifier import Classification
from app.models import AgentDecision, RecoveryAction
from app.rules import HIGH_VALUE_THRESHOLD_INR, MAX_RETRY_ATTEMPTS


def decide_action(
    case_id: str,
    classification: Classification,
    recovery_score: float,
    amount: float,
    retry_count: int,
    bypass_high_value_guardrail: bool = False,
) -> AgentDecision:
    """
    Zero-AI baseline decision. Pure rules, no LLM involved — this is what
    Day 2-3 measures itself against, and what every LLM recommendation must
    still clear via authorize() before execution.

    bypass_high_value_guardrail: used ONLY by the simulated-approval flow
    (Day 9) after a human has approved a high-value case that was
    previously escalated — retry-cap and terminal-case guardrails still
    apply unconditionally either way.
    """
    reasoning_parts = [classification["reason"]]

    # Guardrail: hard retry cap, enforced in code regardless of any score.
    if retry_count >= MAX_RETRY_ATTEMPTS:
        return AgentDecision(
            case_id=case_id,
            recommended_action=RecoveryAction.do_not_retry,
            confidence=1.0,
            recovery_probability=recovery_score,
            reasoning=f"Hard retry cap ({MAX_RETRY_ATTEMPTS}) reached; no further attempts allowed.",
            is_terminal=True,
        )

    # Guardrail: explicit do-not-retry list (terminal / adversarial cases).
    if classification["is_terminal"]:
        return AgentDecision(
            case_id=case_id,
            recommended_action=RecoveryAction.do_not_retry,
            confidence=0.95,
            recovery_probability=recovery_score,
            reasoning=" ".join(reasoning_parts),
            is_terminal=True,
        )

    # Guardrail: high-value transactions require simulated human approval,
    # regardless of how confident the score is — unless that approval has
    # already happened (bypass_high_value_guardrail=True from the /approve
    # endpoint).
    if amount > HIGH_VALUE_THRESHOLD_INR and not bypass_high_value_guardrail:
        return AgentDecision(
            case_id=case_id,
            recommended_action=RecoveryAction.escalate_human_review,
            confidence=0.7,
            recovery_probability=recovery_score,
            reasoning=f"Amount ₹{amount:,.2f} exceeds ₹{HIGH_VALUE_THRESHOLD_INR:,} auto-action threshold.",
            is_terminal=False,
        )

    # Score-banded action selection.
    if recovery_score >= 0.70:
        action = RecoveryAction.immediate_retry
        confidence = 0.85
    elif recovery_score >= 0.45:
        action = RecoveryAction.payment_link
        confidence = 0.65
    elif recovery_score >= 0.25:
        action = RecoveryAction.alternative_method
        confidence = 0.5
    else:
        action = RecoveryAction.escalate_human_review
        confidence = 0.4

    reasoning_parts.append(f"recovery_score={recovery_score:.2f} -> {action.value}")

    return AgentDecision(
        case_id=case_id,
        recommended_action=action,
        confidence=confidence,
        recovery_probability=recovery_score,
        reasoning=" ".join(reasoning_parts),
        is_terminal=False,
    )


def authorize(decision: AgentDecision, amount: float, retry_count: int) -> AgentDecision:
    """
    Guardrail gate for LLM-produced decisions (used from Day 4-6 onward).
    Re-applies the same non-negotiable checks independently of whatever the
    model recommended, and overrides if the model's suggestion would violate
    a guardrail. This is what keeps the LLM from ever taking an unconstrained
    financial action.
    """
    if retry_count >= MAX_RETRY_ATTEMPTS and decision.recommended_action != RecoveryAction.do_not_retry:
        decision.recommended_action = RecoveryAction.do_not_retry
        decision.is_terminal = True
        decision.reasoning += " [OVERRIDDEN by policy: retry cap reached]"

    if amount > HIGH_VALUE_THRESHOLD_INR and decision.recommended_action not in (
        RecoveryAction.escalate_human_review,
        RecoveryAction.do_not_retry,
    ):
        decision.recommended_action = RecoveryAction.escalate_human_review
        decision.reasoning += " [OVERRIDDEN by policy: exceeds high-value threshold]"

    return decision
