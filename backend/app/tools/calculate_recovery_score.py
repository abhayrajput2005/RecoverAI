"""Tool: calculate_recovery_score — Estimate recovery probability."""
from app.classifier import Classification
from app.scoring import calculate_recovery_score as _calculate_recovery_score


def calculate_recovery_score(case_id: str, classification: Classification, customer_history: dict, retry_count: int = 0) -> float:
    return _calculate_recovery_score(classification, customer_history, retry_count)
