from app.scoring import calculate_recovery_score


def _hist(successful=0, failed=0, is_subscription=False):
    return {
        "successful_payments_last_90d": successful,
        "failed_payments_last_90d": failed,
        "is_subscription": is_subscription,
    }


def test_adversarial_case_scores_near_zero_regardless_of_history():
    classification = {"bucket": "adversarial", "is_terminal": True, "reason": "x"}
    # Even a customer with a perfect history must not get talked into a
    # high recovery score on a terminal case.
    score = calculate_recovery_score(classification, _hist(successful=12, failed=0, is_subscription=True), retry_count=0)
    assert score <= 0.05


def test_clear_case_with_good_history_scores_high():
    classification = {"bucket": "clear", "is_terminal": False, "reason": "x"}
    score = calculate_recovery_score(classification, _hist(successful=8, failed=0, is_subscription=True), retry_count=0)
    assert score > 0.75


def test_score_is_clamped_to_one():
    classification = {"bucket": "clear", "is_terminal": False, "reason": "x"}
    score = calculate_recovery_score(classification, _hist(successful=50, failed=0, is_subscription=True), retry_count=0)
    assert score <= 1.0


def test_score_is_clamped_to_zero():
    classification = {"bucket": "edge", "is_terminal": False, "reason": "x"}
    score = calculate_recovery_score(classification, _hist(successful=0, failed=5, is_subscription=False), retry_count=3)
    assert score >= 0.0


def test_more_retries_lowers_score():
    classification = {"bucket": "ambiguous", "is_terminal": False, "reason": "x"}
    hist = _hist(successful=2, failed=1)
    low_retry = calculate_recovery_score(classification, hist, retry_count=0)
    high_retry = calculate_recovery_score(classification, hist, retry_count=2)
    assert high_retry < low_retry


def test_more_recent_failures_lowers_score():
    classification = {"bucket": "clear", "is_terminal": False, "reason": "x"}
    good = calculate_recovery_score(classification, _hist(successful=5, failed=0), retry_count=0)
    bad = calculate_recovery_score(classification, _hist(successful=5, failed=4), retry_count=0)
    assert bad < good
