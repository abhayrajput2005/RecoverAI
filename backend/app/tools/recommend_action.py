"""Tool: recommend_action — Choose the next best recovery action."""
from app.audit import log_decision
from app.classifier import Classification
from app.models import AgentDecision
from app.policy import authorize, decide_action


def recommend_action(
    case_id: str,
    recovery_score: float,
    classification: Classification,
    amount: float,
    retry_count: int,
    gateway_message: str = "",
    failure_code: str = "",
    customer_history: dict = None,
) -> AgentDecision:
    """
    Day 2-3: pure rule-based decision via app/policy.py for clear/edge/
    adversarial cases (zero AI).

    Day 4-6: for classification['bucket'] == 'ambiguous', route to the
    Gemini agent instead — it's the only bucket the LLM ever touches.
    Either way, the result is passed through app.policy.authorize() before
    being returned, so guardrails apply regardless of which path produced
    the recommendation.
    """
    customer_history = customer_history or {}

    if classification["bucket"] == "ambiguous":
        from app.agent import recommend_action_llm  # lazy import: avoids requiring
                                                       # GEMINI_API_KEY for non-ambiguous cases
        decision = recommend_action_llm(
            case_id, classification, gateway_message, failure_code, amount, retry_count, customer_history
        )
        log_decision(case_id, "llm", decision.model_dump())
    else:
        decision = decide_action(case_id, classification, recovery_score, amount, retry_count)
        log_decision(case_id, "deterministic", decision.model_dump())

    authorized = authorize(decision, amount, retry_count)
    if authorized.reasoning != decision.reasoning:
        log_decision(case_id, "policy_override", authorized.model_dump())

    return authorized
