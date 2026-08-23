"""
Persistence layer (Day 7-8). SQLite for local dev, trivially swappable for
Postgres on the deployed demo (report Section 6) — just change DATABASE_URL.

This is what makes idempotency and cooldown enforcement possible: without a
durable case_status + last_action_at, create_retry_or_payment_link() has no
way to know "have I already acted on this case, and how recently."
"""

import os
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app import config  # noqa: F401 - load backend/.env before reading env vars

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./recoverai.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class CaseRecord(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True)
    payment_id = Column(String, index=True)
    customer_id = Column(String, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    payment_method = Column(String)
    failed_at = Column(DateTime)
    failure_code = Column(String)
    gateway_message = Column(String)
    retry_count = Column(Integer, default=0)

    successful_payments_last_90d = Column(Integer, default=0)
    failed_payments_last_90d = Column(Integer, default=0)
    is_subscription = Column(Boolean, default=False)

    # Mutable recovery-loop state
    status = Column(String, default="pending")  # see CaseStatus enum in app/models.py
    last_action = Column(String, nullable=True)
    last_action_at = Column(DateTime, nullable=True)
    razorpay_reference_id = Column(String, nullable=True)  # order_id or payment_link id
    recovered_amount = Column(Float, nullable=True)

    # Evaluation-only fields — never shown to the classifier/agent, used
    # purely for the metrics in app/metrics.py
    classification_bucket = Column(String, nullable=True)  # what the classifier predicted
    ground_truth_bucket = Column(String, nullable=True)    # dataset's known-correct label


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()


def utcnow():
    return datetime.now(timezone.utc)
