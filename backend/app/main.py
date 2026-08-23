from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.audit import log_decision, read_audit_log
from app.db import CaseRecord, get_session, init_db
from app.metrics import compute_metrics
from app.models import CaseOutcome, CaseStatus, RecoveryAction
from app.pipeline import approve_case, process_case
from app.razorpay_client import verify_webhook_signature
from app.tools.record_outcome import record_outcome

app = FastAPI(
    title="RecoverAI",
    description="AI-powered payment revenue recovery agent",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before deploying
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/cases")
def list_cases():
    session = get_session()
    try:
        cases = session.query(CaseRecord).all()
        return {
            "cases": [
                {
                    "case_id": c.case_id,
                    "amount": c.amount,
                    "status": c.status,
                    "failure_code": c.failure_code,
                    "retry_count": c.retry_count,
                    "last_action": c.last_action,
                    "recovered_amount": c.recovered_amount,
                    "classification_bucket": c.classification_bucket,
                }
                for c in cases
            ]
        }
    finally:
        session.close()


@app.get("/audit-log")
def audit_log():
    return {"entries": read_audit_log()}


@app.get("/metrics")
def metrics():
    """Report Section 8's recovery-rate / accuracy / false-positive-cost metrics."""
    return compute_metrics()


@app.post("/cases/{case_id}/process")
def process_case_endpoint(case_id: str):
    """
    Runs the full closed loop for one case: classify -> score -> decide ->
    either auto-execute or route to 'in_review' for high-value approval.
    """
    try:
        return process_case(case_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/cases/{case_id}/approve")
def approve_case_endpoint(case_id: str):
    """
    Simulated human-approval step for a case sitting in 'in_review'
    (report Section 5: no high-value action without approval).
    """
    try:
        return approve_case(case_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request):
    """
    Handles Razorpay webhook events for payment status changes (report
    Section 7 tech stack: 'webhooks for status'). Configure this URL in the
    Razorpay dashboard under Settings -> Webhooks, subscribed to at least
    payment.captured, payment.failed, and payment_link.paid.
    """
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("event")

    # Notes set in razorpay_client.create_order / create_payment_link carry
    # case_id through so we can map the webhook back to a recovery case.
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {}) or \
        payload.get("payload", {}).get("payment_link", {}).get("entity", {})
    notes = entity.get("notes", {})
    case_id = notes.get("case_id")

    log_decision(case_id or "unknown", "webhook", {"event": event, "raw_notes": notes})

    if not case_id:
        return {"received": True, "matched_case": False}

    if event in ("payment.captured", "payment_link.paid"):
        record_outcome(CaseOutcome(
            case_id=case_id,
            action_taken=RecoveryAction(notes.get("action", "immediate_retry")),
            status=CaseStatus.recovered,
            recovered_amount=entity.get("amount", 0) / 100,
            executed_at=datetime.now(timezone.utc),
        ))
    elif event == "payment.failed":
        record_outcome(CaseOutcome(
            case_id=case_id,
            action_taken=RecoveryAction(notes.get("action", "immediate_retry")),
            status=CaseStatus.failed,
            executed_at=datetime.now(timezone.utc),
        ))

    return {"received": True, "matched_case": True, "case_id": case_id}
