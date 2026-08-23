"""Tool: analyze_failure — Classify the failure / recovery situation."""
from app.classifier import Classification, classify_failure


def analyze_failure(failure_code: str, gateway_message: str, retry_count: int) -> Classification:
    """
    Deterministic classification (Day 2-3 core). Ambiguous cases are
    returned as bucket='ambiguous' — Day 4-6 wires an LLM call in front of
    this only for that bucket, using gateway_message as free-text context.
    """
    return classify_failure(failure_code, gateway_message, retry_count)
