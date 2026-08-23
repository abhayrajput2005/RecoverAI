import pytest

from app.classifier import classify_failure


def test_terminal_code_is_adversarial():
    result = classify_failure("CARD_REPORTED_LOST", "Card reported lost", 0)
    assert result["bucket"] == "adversarial"
    assert result["is_terminal"] is True


def test_fraud_flag_is_adversarial_even_with_zero_retries():
    result = classify_failure("FRAUD_FLAG", "Flagged for fraud", 0)
    assert result["bucket"] == "adversarial"
    assert result["is_terminal"] is True


def test_retry_cap_forces_edge_terminal_regardless_of_code():
    # Even a normally "clear" code becomes a forced-terminal edge case once
    # the hard retry cap is hit.
    result = classify_failure("INSUFFICIENT_FUNDS", "no balance", 3)
    assert result["bucket"] == "edge"
    assert result["is_terminal"] is True


def test_clear_code_under_retry_cap_is_not_terminal():
    result = classify_failure("CARD_EXPIRED", "Card expired", 1)
    assert result["bucket"] == "clear"
    assert result["is_terminal"] is False


def test_known_edge_code_is_edge_not_terminal():
    result = classify_failure("CHURNED_CUSTOMER", "subscription cancelled", 0)
    assert result["bucket"] == "edge"
    assert result["is_terminal"] is False


def test_unknown_code_falls_through_to_ambiguous():
    result = classify_failure("SOME_NEW_GATEWAY_CODE", "weird message", 0)
    assert result["bucket"] == "ambiguous"
    assert result["is_terminal"] is False


def test_terminal_code_wins_over_retry_cap_reason():
    # Both conditions true — terminal code check must run first so the
    # audit trail reason references the do-not-retry list, not the cap.
    result = classify_failure("ACCOUNT_CLOSED", "account closed", 5)
    assert result["bucket"] == "adversarial"
    assert "do-not-retry list" in result["reason"]
