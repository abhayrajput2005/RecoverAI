"""
Day 9 — computed metrics from real DB state (report Section 8's metrics
table), as opposed to scripts/baseline_metrics.py which runs a one-off
pass over the raw dataset. This reflects whatever's actually happened to
cases processed through app/pipeline.py so far.
"""

from app.db import CaseRecord, get_session

EXECUTED_STATUSES = {"action_taken", "recovered", "failed"}


def compute_metrics() -> dict:
    session = get_session()
    try:
        cases = session.query(CaseRecord).all()
        total = len(cases)

        eligible = [c for c in cases if c.status != "do_not_retry"]
        recovered = [c for c in cases if c.status == "recovered"]
        executed = [c for c in cases if c.status in EXECUTED_STATUSES]

        total_failed_revenue = sum(c.amount for c in cases)
        potentially_recoverable_revenue = sum(c.amount for c in eligible)
        recovered_revenue = sum((c.recovered_amount or 0) for c in recovered)

        recovery_rate = len(recovered) / len(eligible) if eligible else 0.0
        action_success_rate = len(recovered) / len(executed) if executed else 0.0

        # Agent accuracy: predicted bucket vs dataset ground truth, for
        # cases that have actually been processed (classification_bucket set).
        classified = [c for c in cases if c.classification_bucket is not None and c.ground_truth_bucket is not None]
        agreement = sum(1 for c in classified if c.classification_bucket == c.ground_truth_bucket)
        agent_accuracy = agreement / len(classified) if classified else None

        # False-positive cost: value of adversarial (ground-truth terminal)
        # cases that somehow did NOT end up blocked. Should always be 0 —
        # this is the guardrail-failure canary metric.
        false_positive_cases = [
            c for c in cases
            if c.ground_truth_bucket == "adversarial" and c.status != "do_not_retry"
        ]
        false_positive_cost = sum(c.amount for c in false_positive_cases)

        return {
            "total_cases": total,
            "total_failed_revenue": round(total_failed_revenue, 2),
            "potentially_recoverable_revenue": round(potentially_recoverable_revenue, 2),
            "recovered_revenue": round(recovered_revenue, 2),
            "recovery_rate": round(recovery_rate, 4),
            "action_success_rate": round(action_success_rate, 4),
            "agent_accuracy": round(agent_accuracy, 4) if agent_accuracy is not None else None,
            "agent_accuracy_n": len(classified),
            "false_positive_cost": round(false_positive_cost, 2),
            "false_positive_case_ids": [c.case_id for c in false_positive_cases],
            "status_breakdown": _status_breakdown(cases),
        }
    finally:
        session.close()


def _status_breakdown(cases) -> dict:
    breakdown = {}
    for c in cases:
        breakdown[c.status] = breakdown.get(c.status, 0) + 1
    return breakdown
