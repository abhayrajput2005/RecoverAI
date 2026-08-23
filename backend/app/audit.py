"""
Audit trail — every tool call and every decision (deterministic or LLM)
gets logged here. Report Section 4: "Every tool call is logged." and
Section 12 deliverable: a documented exception list / decision audit trail.

Deliberately simple (append-only JSONL) since this is a 12-day solo build,
not a production logging pipeline — good enough to power the dashboard's
audit view (Section 9) and demo (Section 11: "Show the audit trail").
"""

import json
import os
from datetime import datetime, timezone

_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "audit_log.jsonl")


def log_decision(case_id: str, source: str, payload: dict) -> None:
    """
    source: 'deterministic' | 'llm' | 'policy_override' | 'execution'
    payload: whatever's relevant to log for that source (decision fields,
    override reason, execution result, etc.)
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "case_id": case_id,
        "source": source,
        "payload": payload,
    }
    with open(_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_audit_log() -> list:
    if not os.path.exists(_LOG_PATH):
        return []
    with open(_LOG_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]
