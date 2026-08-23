"""
Razorpay integration (Day 7-8, report Section 6: "test mode — Orders,
Payments, Payment Links, Webhooks").

This is the ONLY module that talks to the Razorpay SDK directly. Every
call here is in test mode — RAZORPAY_KEY_ID/SECRET should be your test-mode
keys from the Razorpay dashboard, never live keys, for a buildathon demo.
"""

import os

import razorpay


def _get_client() -> razorpay.Client:
    key_id = os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise RuntimeError(
            "RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET not set. Copy backend/.env.example "
            "to backend/.env and add your TEST MODE keys from the Razorpay dashboard "
            "(Settings -> API Keys)."
        )
    client = razorpay.Client(auth=(key_id, key_secret))
    return client


def create_order(amount_inr: float, receipt: str, notes: dict = None) -> dict:
    """
    Creates a test-mode Order for a retry attempt. Amount must be in paise
    (smallest currency unit) per Razorpay's API.
    """
    client = _get_client()
    order = client.order.create({
        "amount": int(round(amount_inr * 100)),
        "currency": "INR",
        "receipt": receipt,
        "notes": notes or {},
    })
    return order


def create_payment_link(amount_inr: float, description: str, customer_id: str, notes: dict = None) -> dict:
    """
    Creates a test-mode Payment Link — used for the 'payment_link' and
    'alternative_method' recovery actions, where we want a shareable link
    rather than an immediate silent retry.
    """
    client = _get_client()
    link = client.payment_link.create({
        "amount": int(round(amount_inr * 100)),
        "currency": "INR",
        "description": description,
        "notes": {**(notes or {}), "recoverai_customer_id": customer_id},
        "notify": {"sms": False, "email": False},  # off for test-mode demo; toggle on for real notify
        "reminder_enable": True,
    })
    return link


def verify_webhook_signature(payload_body: bytes, signature: str) -> bool:
    """
    Verifies an incoming webhook actually came from Razorpay before trusting
    its contents to update any case status.
    """
    webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET")
    if not webhook_secret:
        raise RuntimeError("RAZORPAY_WEBHOOK_SECRET not set in backend/.env")

    client = _get_client()
    try:
        client.utility.verify_webhook_signature(payload_body.decode(), signature, webhook_secret)
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
