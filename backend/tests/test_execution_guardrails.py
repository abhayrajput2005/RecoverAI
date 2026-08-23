"""
Tests for create_retry_or_payment_link's guardrails (report Section 14 risk:
"Duplicate recovery actions" -> mitigation: "Idempotency + transaction-state
checks"). Uses an isolated in-memory SQLite DB and mocks the Razorpay SDK
calls so no network/API key is needed.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db as db_module
from app.db import Base, CaseRecord, utcnow
from app.models import RecoveryAction
from app.tools.create_retry_or_payment_link import (
    CooldownError,
    IdempotencyError,
    create_retry_or_payment_link,
)


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """Point the DB module at a fresh in-memory SQLite DB for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(db_module, "SessionLocal", TestSession)
    yield


def _make_case(case_id="RC-1", status="pending", last_action_at=None, retry_count=0):
    session = db_module.get_session()
    case = CaseRecord(
        case_id=case_id,
        payment_id="pay_test",
        customer_id="cust_test",
        amount=1000.0,
        currency="INR",
        payment_method="card",
        failed_at=utcnow(),
        failure_code="CARD_EXPIRED",
        gateway_message="expired",
        retry_count=retry_count,
        status=status,
        last_action_at=last_action_at,
    )
    session.add(case)
    session.commit()
    session.close()


def test_non_executable_action_is_a_noop_and_never_calls_razorpay():
    _make_case()
    with patch("app.tools.create_retry_or_payment_link.create_order") as mock_order:
        result = create_retry_or_payment_link("RC-1", RecoveryAction.do_not_retry)
        mock_order.assert_not_called()
        assert result["executed"] is False


def test_immediate_retry_calls_create_order_and_updates_status():
    _make_case()
    with patch(
        "app.tools.create_retry_or_payment_link.create_order",
        return_value={"id": "order_fake123"},
    ) as mock_order:
        result = create_retry_or_payment_link("RC-1", RecoveryAction.immediate_retry)
        mock_order.assert_called_once()
        assert result["executed"] is True
        assert result["razorpay_reference_id"] == "order_fake123"

    session = db_module.get_session()
    case = session.query(CaseRecord).filter_by(case_id="RC-1").one()
    assert case.status == "action_taken"
    assert case.retry_count == 1
    session.close()


def test_already_actioned_case_raises_idempotency_error():
    _make_case(status="action_taken", last_action_at=utcnow() - timedelta(hours=100))
    with patch("app.tools.create_retry_or_payment_link.create_order") as mock_order:
        with pytest.raises(IdempotencyError):
            create_retry_or_payment_link("RC-1", RecoveryAction.immediate_retry)
        mock_order.assert_not_called()


def test_recent_action_within_cooldown_raises_cooldown_error():
    # last_action_at just 1 hour ago, cooldown is several hours per app/rules.py
    _make_case(status="pending", last_action_at=utcnow() - timedelta(hours=1))
    with patch("app.tools.create_retry_or_payment_link.create_order") as mock_order:
        with pytest.raises(CooldownError):
            create_retry_or_payment_link("RC-1", RecoveryAction.immediate_retry)
        mock_order.assert_not_called()


def test_action_outside_cooldown_window_is_allowed():
    from app.rules import COOLDOWN_HOURS
    _make_case(status="pending", last_action_at=utcnow() - timedelta(hours=COOLDOWN_HOURS + 1))
    with patch(
        "app.tools.create_retry_or_payment_link.create_order",
        return_value={"id": "order_fake456"},
    ) as mock_order:
        result = create_retry_or_payment_link("RC-1", RecoveryAction.immediate_retry)
        mock_order.assert_called_once()
        assert result["executed"] is True


def test_payment_link_action_calls_create_payment_link_not_create_order():
    _make_case()
    with patch(
        "app.tools.create_retry_or_payment_link.create_payment_link",
        return_value={"id": "plink_fake789"},
    ) as mock_link, patch("app.tools.create_retry_or_payment_link.create_order") as mock_order:
        result = create_retry_or_payment_link("RC-1", RecoveryAction.payment_link)
        mock_link.assert_called_once()
        mock_order.assert_not_called()
        assert result["razorpay_reference_id"] == "plink_fake789"
