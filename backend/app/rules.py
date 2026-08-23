"""
Constants shared by the deterministic classifier, scorer, and policy engine.

These encode the report's Section 5 guardrails and Section 7 failure-code
taxonomy. Keeping them in one place means the policy engine and the dataset
generator can't silently drift apart.
"""

# Codes that are always terminal — the do-not-retry list (report Section 5).
TERMINAL_CODES = {
    "CARD_REPORTED_LOST",
    "CARD_REPORTED_LOST_2",
    "ACCOUNT_CLOSED",
    "FRAUD_FLAG",
}

# Codes with an obvious, unambiguous right action.
CLEAR_CODES = {
    "INSUFFICIENT_FUNDS",
    "CARD_EXPIRED",
    "BANK_DECLINE_GENERIC",
    "UPI_MANDATE_TIMEOUT",
}

# Codes that are structurally edge cases regardless of message content.
EDGE_CODES = {
    "DUPLICATE_CHARGE_ATTEMPT",
    "MAX_RETRIES_EXCEEDED",
    "CHURNED_CUSTOMER",
    "MANDATE_CANCELLED",
}

# Anything not in the above three sets is treated as ambiguous and, from
# Day 4-6 onward, routed to the LLM for judgment.

# --- Guardrails (report Section 5, non-negotiable) ---
MAX_RETRY_ATTEMPTS = 3
COOLDOWN_HOURS = 6
HIGH_VALUE_THRESHOLD_INR = 10_000  # requires simulated approval above this
