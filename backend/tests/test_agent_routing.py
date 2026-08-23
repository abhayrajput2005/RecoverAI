"""
Tests the routing logic in app/tools/recommend_action.py without making a
real Gemini API call — the LLM call itself is mocked out, since what needs
testing here is "does an ambiguous case get routed to the LLM path, and
does policy.authorize() still catch a bad LLM recommendation," not
Gemini's actual judgment quality (which needs a live key and manual
evaluation, not a unit test).
"""

from unittest.mock import patch

from app.models import AgentDecision, RecoveryAction
from app.tools.recommend_action import recommend_action


def test_clear_case_never_calls_the_llm():
    classification = {"bucket": "clear", "is_terminal": False, "reason": "x"}
    with patch("app.agent.recommend_action_llm") as mock_llm:
        decision = recommend_action(
            "RC-1", recovery_score=0.8, classification=classification, amount=500, retry_count=0
        )
        mock_llm.assert_not_called()
        assert decision.recommended_action == RecoveryAction.immediate_retry


def test_adversarial_case_never_calls_the_llm():
    classification = {"bucket": "adversarial", "is_terminal": True, "reason": "x"}
    with patch("app.agent.recommend_action_llm") as mock_llm:
        decision = recommend_action(
            "RC-2", recovery_score=0.02, classification=classification, amount=500, retry_count=0
        )
        mock_llm.assert_not_called()
        assert decision.recommended_action == RecoveryAction.do_not_retry


def test_ambiguous_case_routes_to_llm():
    classification = {"bucket": "ambiguous", "is_terminal": False, "reason": "x"}
    fake_decision = AgentDecision(
        case_id="RC-3",
        recommended_action=RecoveryAction.payment_link,
        confidence=0.6,
        recovery_probability=0.5,
        reasoning="mocked LLM reasoning",
        is_terminal=False,
    )
    with patch("app.agent.recommend_action_llm", return_value=fake_decision) as mock_llm:
        decision = recommend_action(
            "RC-3", recovery_score=0.5, classification=classification, amount=500, retry_count=0,
            gateway_message="vague error", failure_code="UNKNOWN_DECLINE", customer_history={},
        )
        mock_llm.assert_called_once()
        assert decision.recommended_action == RecoveryAction.payment_link


def test_policy_still_overrides_a_bad_llm_recommendation_on_ambiguous_case():
    # Guardrail check: even if the LLM (mocked here) recommends immediate_retry
    # on a case that has already hit the retry cap, authorize() must override it.
    classification = {"bucket": "ambiguous", "is_terminal": False, "reason": "x"}
    overconfident_llm_decision = AgentDecision(
        case_id="RC-4",
        recommended_action=RecoveryAction.immediate_retry,
        confidence=0.9,
        recovery_probability=0.9,
        reasoning="LLM ignored the retry cap",
        is_terminal=False,
    )
    with patch("app.agent.recommend_action_llm", return_value=overconfident_llm_decision):
        decision = recommend_action(
            "RC-4", recovery_score=0.9, classification=classification, amount=500, retry_count=3,
            gateway_message="vague error", failure_code="UNKNOWN_DECLINE", customer_history={},
        )
        assert decision.recommended_action == RecoveryAction.do_not_retry
        assert "OVERRIDDEN" in decision.reasoning
