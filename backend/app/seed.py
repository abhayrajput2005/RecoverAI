"""
Safe startup seeding for RecoverAI.

Seeds the demo dataset only when the cases table is empty.
Existing cases are never deleted, reset, or overwritten.
"""

import json
from datetime import datetime
from pathlib import Path

from app.db import CaseRecord, get_session


def seed_if_empty():
    session = get_session()

    try:
        # IMPORTANT:
        # If even one case exists, never touch the database.
        existing_count = session.query(CaseRecord).count()

        if existing_count > 0:
            return 0

        dataset_path = (
            Path(__file__).resolve().parent.parent
            / "dataset"
            / "payments.json"
        )

        if not dataset_path.exists():
            raise FileNotFoundError(
                f"Demo dataset not found: {dataset_path}"
            )

        with dataset_path.open("r", encoding="utf-8") as f:
            records = json.load(f)

        for r in records:
            case = CaseRecord(
                case_id=r["case_id"],
                payment_id=r["payment_id"],
                customer_id=r["customer_id"],
                amount=r["amount"],
                currency=r["currency"],
                payment_method=r["payment_method"],
                failed_at=datetime.fromisoformat(
                    r["failed_at"].replace("Z", "+00:00")
                ),
                failure_code=r["failure_code"],
                gateway_message=r["gateway_message"],
                retry_count=r["retry_count"],
                successful_payments_last_90d=(
                    r["customer_history"]["successful_payments_last_90d"]
                ),
                failed_payments_last_90d=(
                    r["customer_history"]["failed_payments_last_90d"]
                ),
                is_subscription=(
                    r["customer_history"]["is_subscription"]
                ),
                status="pending",
                ground_truth_bucket=r.get("bucket_label"),
            )

            session.add(case)

        session.commit()

        return len(records)

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()