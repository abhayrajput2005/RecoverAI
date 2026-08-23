"""
RecoverAI — Synthetic Payment Dataset Generator (Day 1 deliverable)

Generates N synthetic "failed/at-risk payment" records split into four
buckets, matching Section 7 of the project report:

    Clear (~40%)       - unambiguous decline codes, obvious right action
    Ambiguous (~30%)   - vague gateway messages / free-text notes needing
                          LLM judgment
    Edge (~20%)        - duplicates, already-retried-too-many-times,
                          churned customers, cancelled mandates
    Adversarial (~10%) - look recoverable but are terminal (e.g. card
                          reported lost) — proves guardrails work

Usage:
    python generate_dataset.py --count 100 --seed 42 --out payments.json
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone

CURRENCY = "INR"

CLEAR_REASONS = [
    ("INSUFFICIENT_FUNDS", "Insufficient balance in account"),
    ("CARD_EXPIRED", "Card expired"),
    ("BANK_DECLINE_GENERIC", "Declined by issuing bank"),
    ("UPI_MANDATE_TIMEOUT", "UPI mandate approval timed out"),
]

AMBIGUOUS_REASONS = [
    ("GATEWAY_ERROR_5XX", "Payment could not be processed at this time"),
    ("CHECKOUT_ABANDONED", "Customer closed checkout before completing payment"),
    ("UNKNOWN_DECLINE", "Transaction declined — no reason provided by bank"),
    ("NETWORK_TIMEOUT", "Request timed out during authorization"),
]

EDGE_REASONS = [
    ("DUPLICATE_CHARGE_ATTEMPT", "Possible duplicate of a recent successful payment"),
    ("MAX_RETRIES_EXCEEDED", "Payment already retried 3+ times with no success"),
    ("CHURNED_CUSTOMER", "Customer subscription cancelled prior to this charge"),
    ("MANDATE_CANCELLED", "UPI/e-mandate was cancelled by the customer"),
]

ADVERSARIAL_REASONS = [
    ("CARD_REPORTED_LOST", "Card reported lost/stolen by cardholder"),
    ("ACCOUNT_CLOSED", "Bank account closed"),
    ("FRAUD_FLAG", "Transaction flagged for suspected fraud"),
    ("CARD_REPORTED_LOST_2", "Issuer confirms card blocked — lost/stolen report on file"),
]

FAILURE_TYPES = {
    "clear": CLEAR_REASONS,
    "ambiguous": AMBIGUOUS_REASONS,
    "edge": EDGE_REASONS,
    "adversarial": ADVERSARIAL_REASONS,
}

BUCKET_WEIGHTS = {
    "clear": 0.40,
    "ambiguous": 0.30,
    "edge": 0.20,
    "adversarial": 0.10,
}

PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet"]


def random_amount():
    # skew toward smaller amounts with occasional high-value cases
    if random.random() < 0.1:
        return round(random.uniform(8000, 25000), 2)
    return round(random.uniform(150, 7500), 2)


def random_timestamp(days_back=30):
    now = datetime.now(timezone.utc)
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return (now - delta).isoformat().replace("+00:00", "Z")


def build_record(bucket: str, index: int) -> dict:
    code, message = random.choice(FAILURE_TYPES[bucket])
    customer_id = f"cust_{uuid.uuid4().hex[:8]}"
    retry_count = {
        "clear": random.randint(0, 1),
        "ambiguous": random.randint(0, 2),
        "edge": random.randint(3, 5),
        "adversarial": random.randint(0, 2),
    }[bucket]

    record = {
        "case_id": f"RC-{1000 + index}",
        "payment_id": f"pay_{uuid.uuid4().hex[:14]}",
        "customer_id": customer_id,
        "amount": random_amount(),
        "currency": CURRENCY,
        "payment_method": random.choice(PAYMENT_METHODS),
        "failed_at": random_timestamp(),
        "failure_code": code,
        "gateway_message": message,
        "retry_count": retry_count,
        "customer_history": {
            "successful_payments_last_90d": random.randint(0, 12),
            "failed_payments_last_90d": random.randint(0, 5),
            "is_subscription": random.random() < 0.6,
        },
        "bucket_label": bucket,  # ground-truth label for evaluation only,
                                  # NOT to be shown to the agent at inference time
    }
    return record


def generate_dataset(count: int) -> list:
    counts = {}
    remaining = count
    buckets = list(BUCKET_WEIGHTS.keys())
    for i, bucket in enumerate(buckets):
        if i == len(buckets) - 1:
            counts[bucket] = remaining
        else:
            n = round(count * BUCKET_WEIGHTS[bucket])
            counts[bucket] = n
            remaining -= n

    records = []
    idx = 0
    for bucket, n in counts.items():
        for _ in range(n):
            records.append(build_record(bucket, idx))
            idx += 1

    random.shuffle(records)
    return records


def main():
    parser = argparse.ArgumentParser(description="Generate RecoverAI synthetic dataset")
    parser.add_argument("--count", type=int, default=100, help="Number of records (50-150 recommended)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--out", type=str, default="payments.json", help="Output JSON file path")
    args = parser.parse_args()

    random.seed(args.seed)
    dataset = generate_dataset(args.count)

    with open(args.out, "w") as f:
        json.dump(dataset, f, indent=2)

    bucket_counts = {}
    for r in dataset:
        bucket_counts[r["bucket_label"]] = bucket_counts.get(r["bucket_label"], 0) + 1

    print(f"Generated {len(dataset)} records -> {args.out}")
    print("Bucket distribution:", bucket_counts)


if __name__ == "__main__":
    main()
