"""
LLM agent layer — Day 4-6.

This module is the ONLY place in the codebase that calls out to Gemini.
It is deliberately narrow in scope: it only ever gets invoked for cases the
deterministic classifier (app/classifier.py) has already labeled
'ambiguous' — clear, edge, and adversarial cases never reach here at all.

Design principle carried over from the report (Section 2): the model
recommends, deterministic application logic authorizes and executes.
recommend_action_llm() below ALWAYS returns a structured AgentDecision via
Gemini's response_schema enforcement — never free text taken as an
executable action — and the caller (app/tools/recommend_action.py) always
passes the result through app.policy.authorize() before it can be used.
"""

import os

from google import genai
from pydantic import BaseModel, Field

from app.classifier import Classification
from app.models import AgentDecision, RecoveryAction

_DEFAULT_MODEL = "gemini-2.5-flash"


class _LLMRecoveryJudgment(BaseModel):
    """Structured schema Gemini is constrained to. Deliberately narrower
    than AgentDecision — the LLM proposes a judgment call, it does not
    decide the final action. app/policy.py maps this to an action."""
    recovery_probability: float = Field(ge=0.0, le=1.0, description="Estimated 0-1 probability this payment is recoverable")
    suggested_urgency: str = Field(description="One of: low, medium, high — how time-sensitive recovery is")
    reasoning: str = Field(description="1-2 sentence explanation grounded in the gateway message and customer history")


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and fill in your key (see README for how to get one)."
        )
    return genai.Client(api_key=api_key)


def judge_ambiguous_case(
    case_id: str,
    gateway_message: str,
    failure_code: str,
    amount: float,
    retry_count: int,
    customer_history: dict,
) -> _LLMRecoveryJudgment:
    """
    Calls Gemini with a constrained response_schema so the output is always
    valid, parseable JSON matching _LLMRecoveryJudgment — never free text.
    """
    client = _get_client()
    model = os.environ.get("GEMINI_MODEL", _DEFAULT_MODEL)

    prompt = f"""You are assessing a single ambiguous failed payment for a
recovery agent. You are NOT authorizing any action — you are only judging
how recoverable this looks based on the evidence given.

Case ID: {case_id}
Failure code: {failure_code}
Gateway message: "{gateway_message}"
Amount: INR {amount:,.2f}
Retries already attempted: {retry_count}
Customer history (last 90 days): {customer_history.get('successful_payments_last_90d', 0)} successful,
  {customer_history.get('failed_payments_last_90d', 0)} failed, subscription={customer_history.get('is_subscription', False)}

Judge the recovery_probability based on how much the gateway message and
customer history suggest this is a genuinely recoverable situation
(temporary, on the customer's side, likely to succeed on retry) versus a
situation that just looks ambiguous but is probably not worth pursuing."""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": _LLMRecoveryJudgment,
        },
    )
    return response.parsed


def recommend_action_llm(
    case_id: str,
    classification: Classification,
    gateway_message: str,
    failure_code: str,
    amount: float,
    retry_count: int,
    customer_history: dict,
) -> AgentDecision:
    """
    Only ever called for classification['bucket'] == 'ambiguous'. Maps the
    LLM's judgment into the same AgentDecision shape the deterministic
    policy engine produces, so both paths are interchangeable to the caller
    — and both still go through app.policy.authorize() afterward.
    """
    judgment = judge_ambiguous_case(
        case_id, gateway_message, failure_code, amount, retry_count, customer_history
    )

    score = judgment.recovery_probability
    if score >= 0.70:
        action = RecoveryAction.immediate_retry
    elif score >= 0.45:
        action = RecoveryAction.payment_link
    elif score >= 0.25:
        action = RecoveryAction.alternative_method
    else:
        action = RecoveryAction.escalate_human_review

    return AgentDecision(
        case_id=case_id,
        recommended_action=action,
        confidence=0.6,  # LLM judgments on ambiguous cases start at moderate confidence
        recovery_probability=score,
        reasoning=f"[Gemini/{os.environ.get('GEMINI_MODEL', _DEFAULT_MODEL)}] {judgment.reasoning} (urgency={judgment.suggested_urgency})",
        is_terminal=False,
    )
