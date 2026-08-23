"""
Deterministic failure classifier — the zero-AI baseline (report Day 2-3).

Rule order matters: terminal codes and retry-cap checks are evaluated first
so they can never be shadowed by a later, looser rule. Only messages that
match none of the known code sets fall through to "ambiguous", which is the
only bucket the LLM agent (Day 4-6) is allowed to touch.
"""

from typing import TypedDict

from app.rules import CLEAR_CODES, EDGE_CODES, MAX_RETRY_ATTEMPTS, TERMINAL_CODES


class Classification(TypedDict):
    bucket: str          # "clear" | "ambiguous" | "edge" | "adversarial"
    is_terminal: bool
    reason: str           # short human-readable justification for the audit trail


def classify_failure(failure_code: str, gateway_message: str, retry_count: int) -> Classification:
    # 1. Hard terminal codes always win, regardless of retry_count.
    if failure_code in TERMINAL_CODES:
        return Classification(
            bucket="adversarial",
            is_terminal=True,
            reason=f"failure_code '{failure_code}' is on the do-not-retry list",
        )

    # 2. Retry cap guardrail — enforced in code, not by the model.
    if retry_count >= MAX_RETRY_ATTEMPTS:
        return Classification(
            bucket="edge",
            is_terminal=True,
            reason=f"retry_count ({retry_count}) has reached the hard cap ({MAX_RETRY_ATTEMPTS})",
        )

    # 3. Known structural edge cases (duplicates, churned, cancelled mandate).
    if failure_code in EDGE_CODES:
        return Classification(
            bucket="edge",
            is_terminal=False,
            reason=f"failure_code '{failure_code}' is a known edge case",
        )

    # 4. Known clear-cut, high-confidence codes.
    if failure_code in CLEAR_CODES:
        return Classification(
            bucket="clear",
            is_terminal=False,
            reason=f"failure_code '{failure_code}' has an unambiguous right action",
        )

    # 5. Everything else needs judgment on the free-text gateway message.
    return Classification(
        bucket="ambiguous",
        is_terminal=False,
        reason="failure_code not in any known rule set; message requires judgment",
    )
