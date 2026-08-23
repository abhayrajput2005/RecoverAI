"""
Core data models for RecoverAI.

These mirror the synthetic dataset schema (backend/dataset/generate_dataset.py)
and the structured output every LLM decision must return (report Section 5:
"Every LLM decision returns a structured object (action, confidence,
reasoning) — never a free-text response taken as an executable action.")
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PaymentMethod(str, Enum):
    card = "card"
    upi = "upi"
    netbanking = "netbanking"
    wallet = "wallet"


class CustomerHistory(BaseModel):
    successful_payments_last_90d: int
    failed_payments_last_90d: int
    is_subscription: bool


class RecoveryCase(BaseModel):
    case_id: str
    payment_id: str
    customer_id: str
    amount: float
    currency: str = "INR"
    payment_method: PaymentMethod
    failed_at: datetime
    failure_code: str
    gateway_message: str
    retry_count: int
    customer_history: CustomerHistory


class RecoveryAction(str, Enum):
    immediate_retry = "immediate_retry"
    scheduled_retry = "scheduled_retry"
    alternative_method = "alternative_method"
    payment_link = "payment_link"
    escalate_human_review = "escalate_human_review"
    do_not_retry = "do_not_retry"


class AgentDecision(BaseModel):
    """
    The ONLY shape an LLM decision is allowed to take. The application layer
    validates and authorizes this — the model recommends, it never executes
    directly (report Section 2, design principle).
    """
    case_id: str
    recommended_action: RecoveryAction
    confidence: float = Field(ge=0.0, le=1.0)
    recovery_probability: float = Field(ge=0.0, le=1.0)
    reasoning: str
    is_terminal: bool = False  # true for adversarial/do-not-retry cases


class CaseStatus(str, Enum):
    pending = "pending"
    ready = "ready"
    in_review = "in_review"
    action_taken = "action_taken"
    recovered = "recovered"
    failed = "failed"
    do_not_retry = "do_not_retry"


class CaseOutcome(BaseModel):
    case_id: str
    action_taken: RecoveryAction
    status: CaseStatus
    recovered_amount: Optional[float] = None
    executed_at: datetime
    notes: Optional[str] = None
