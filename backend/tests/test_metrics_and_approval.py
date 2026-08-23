"""
Day 9 tests: app/metrics.py's arithmetic, and app/pipeline.approve_case's
guardrail (only 'in_review' cases can be approved; approval bypasses the
high-value threshold check but nothing else).
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db as db_module
from app.db import Base, CaseRecord
from app.metrics import compute_metrics
from app.pipeline import approve_case


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(db_module, "SessionLocal", TestSession)
    yield


def _add_case(session, **kwargs):
    defaults = dict(
        case_id="RC-1", payment_id="pay", customer_id="cust", amount=1000.0,
        currency="INR", payment_method="card", failed_at=datetime.now(timezone.utc),
        failure_code="CARD_EXPIRED", gateway_message="expired", retry_count=0,
        status="pending", classification_bucket=None, ground_truth_bucket=None,
        recovered_amount=None,
    )
    defaults.update(kwargs)
    case = CaseRecord(**defaults)
    session.add(case)
    session.commit()
    return case


def test_recovery_rate_excludes_do_not_retry_cases():
    session = db_module.get_session()
    _add_case(session, case_id="RC-1", status="recovered", recovered_amount=1000.0, amount=1000.0)
    _add_case(session, case_id="RC-2", status="do_not_retry", amount=500.0)
    _add_case(session, case_id="RC-3", status="action_taken", amount=800.0)
    session.close()

    m = compute_metrics()
    # eligible = RC-1, RC-3 (RC-2 excluded); recovered = RC-1 only
    assert m["recovery_rate"] == pytest.approx(0.5)
    assert m["recovered_revenue"] == 1000.0
    assert m["potentially_recoverable_revenue"] == 1800.0
    assert m["total_failed_revenue"] == 2300.0


def test_false_positive_cost_flags_adversarial_cases_not_blocked():
    session = db_module.get_session()
    # Correctly blocked adversarial case — should NOT count as false positive.
    _add_case(session, case_id="RC-1", status="do_not_retry", ground_truth_bucket="adversarial", amount=500.0)
    # Guardrail failure: adversarial case that somehow got actioned.
    _add_case(session, case_id="RC-2", status="action_taken", ground_truth_bucket="adversarial", amount=750.0)
    session.close()

    m = compute_metrics()
    assert m["false_positive_cost"] == 750.0
    assert m["false_positive_case_ids"] == ["RC-2"]


def test_agent_accuracy_ignores_unprocessed_cases():
    session = db_module.get_session()
    _add_case(session, case_id="RC-1", classification_bucket="clear", ground_truth_bucket="clear")
    _add_case(session, case_id="RC-2", classification_bucket="edge", ground_truth_bucket="clear")
    _add_case(session, case_id="RC-3")  # never processed — no classification_bucket
    session.close()

    m = compute_metrics()
    assert m["agent_accuracy_n"] == 2
    assert m["agent_accuracy"] == pytest.approx(0.5)


def test_approve_case_rejects_case_not_in_review():
    session = db_module.get_session()
    _add_case(session, case_id="RC-1", status="pending", failure_code="CARD_EXPIRED", amount=15000.0)
    session.close()

    with pytest.raises(ValueError, match="not awaiting review"):
        approve_case("RC-1")


def test_approve_case_executes_high_value_case_after_approval():
    session = db_module.get_session()
    _add_case(session, case_id="RC-1", status="in_review", failure_code="CARD_EXPIRED", amount=15000.0)
    session.close()

    with patch(
        "app.pipeline.create_retry_or_payment_link",
        return_value={"executed": True, "razorpay_reference_id": "order_fake"},
    ) as mock_exec:
        result = approve_case("RC-1")
        mock_exec.assert_called_once()
        assert result["executed"] is True
