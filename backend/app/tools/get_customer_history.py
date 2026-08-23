"""Tool: get_customer_history — Fetch previous successful and failed attempts."""
from app.db import CaseRecord, get_session
from app.models import CustomerHistory


def get_customer_history(customer_id: str) -> CustomerHistory:
    session = get_session()
    try:
        cases = session.query(CaseRecord).filter_by(customer_id=customer_id).all()
        if not cases:
            return CustomerHistory(
                successful_payments_last_90d=0, failed_payments_last_90d=0, is_subscription=False
            )
        # Cases share the same seeded history snapshot; take the most recent record.
        latest = max(cases, key=lambda c: c.failed_at)
        return CustomerHistory(
            successful_payments_last_90d=latest.successful_payments_last_90d,
            failed_payments_last_90d=latest.failed_payments_last_90d,
            is_subscription=latest.is_subscription,
        )
    finally:
        session.close()
