"""
Loads dataset/payments.json into the cases table as fresh 'pending' cases.
Run this once after generating the dataset, and again anytime you want a
clean slate for a demo run.

Usage:
    python scripts/seed_db.py --dataset dataset/payments.json
"""

import argparse
import json
from datetime import datetime

from app.db import CaseRecord, get_session, init_db


def seed(dataset_path: str, reset: bool = True):
    init_db()
    session = get_session()

    if reset:
        session.query(CaseRecord).delete()
        session.commit()

    with open(dataset_path) as f:
        records = json.load(f)

    for r in records:
        case = CaseRecord(
            case_id=r["case_id"],
            payment_id=r["payment_id"],
            customer_id=r["customer_id"],
            amount=r["amount"],
            currency=r["currency"],
            payment_method=r["payment_method"],
            failed_at=datetime.fromisoformat(r["failed_at"].replace("Z", "+00:00")),
            failure_code=r["failure_code"],
            gateway_message=r["gateway_message"],
            retry_count=r["retry_count"],
            successful_payments_last_90d=r["customer_history"]["successful_payments_last_90d"],
            failed_payments_last_90d=r["customer_history"]["failed_payments_last_90d"],
            is_subscription=r["customer_history"]["is_subscription"],
            status="pending",
            ground_truth_bucket=r.get("bucket_label"),  # evaluation-only; never shown to the agent
        )
        session.merge(case)

    session.commit()
    count = session.query(CaseRecord).count()
    session.close()
    print(f"Seeded {count} cases into the database.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="dataset/payments.json")
    parser.add_argument("--no-reset", action="store_true", help="Don't clear existing cases first")
    args = parser.parse_args()
    seed(args.dataset, reset=not args.no_reset)
