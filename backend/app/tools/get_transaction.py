"""Tool: get_transaction — Fetch transaction / payment context."""
from app.db import CaseRecord, get_session
from app.models import CustomerHistory, PaymentMethod, RecoveryCase


def get_transaction(payment_id: str) -> RecoveryCase:
    session = get_session()
    try:
        case = session.query(CaseRecord).filter_by(payment_id=payment_id).one_or_none()
        if case is None:
            raise ValueError(f"No case found for payment_id: {payment_id}")
        return RecoveryCase(
            case_id=case.case_id,
            payment_id=case.payment_id,
            customer_id=case.customer_id,
            amount=case.amount,
            currency=case.currency,
            payment_method=PaymentMethod(case.payment_method),
            failed_at=case.failed_at,
            failure_code=case.failure_code,
            gateway_message=case.gateway_message,
            retry_count=case.retry_count,
            customer_history=CustomerHistory(
                successful_payments_last_90d=case.successful_payments_last_90d,
                failed_payments_last_90d=case.failed_payments_last_90d,
                is_subscription=case.is_subscription,
            ),
        )
    finally:
        session.close()
