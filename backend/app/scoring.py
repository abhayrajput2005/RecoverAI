"""
Deterministic recovery-score calculator — the zero-AI baseline for the
"Predict" step (report Section 2).

This is intentionally a simple, explainable weighted formula rather than a
trained model — the report is explicit that there's no separate ML model in
this build (Section 6: "no separate ML model"). Score is clamped to [0, 1].
"""

from app.classifier import Classification

_BASE_SCORE_BY_BUCKET = {
    "clear": 0.75,
    "ambiguous": 0.50,
    "edge": 0.30,
    "adversarial": 0.02,
}


def calculate_recovery_score(
    classification: Classification,
    customer_history: dict,
    retry_count: int,
) -> float:
    if classification["is_terminal"]:
        # Terminal cases get a floor score regardless of history — a good
        # customer history should never talk the system into retrying a
        # lost/stolen card. This is what the adversarial test cases in the
        # dataset are designed to catch.
        return _BASE_SCORE_BY_BUCKET["adversarial"] if classification["bucket"] == "adversarial" else 0.05

    score = _BASE_SCORE_BY_BUCKET[classification["bucket"]]

    successful = customer_history.get("successful_payments_last_90d", 0)
    failed = customer_history.get("failed_payments_last_90d", 0)
    is_subscription = customer_history.get("is_subscription", False)

    # Good recent payment history nudges the score up.
    score += min(successful, 10) * 0.01

    # Repeated recent failures (independent of this case's retry_count)
    # nudge the score down.
    score -= min(failed, 5) * 0.03

    # Active subscribers are statistically more likely to want the payment
    # to succeed (they signed up for recurring billing).
    if is_subscription:
        score += 0.03

    # Each retry already attempted on *this* case reduces marginal odds of
    # the next attempt succeeding.
    score -= retry_count * 0.05

    return max(0.0, min(1.0, round(score, 4)))
