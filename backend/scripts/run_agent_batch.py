"""
Day 4-6 batch runner. Requires a real GEMINI_API_KEY in backend/.env —
this is the script that actually calls Gemini for every 'ambiguous' case
and writes the full audit trail.

Unlike scripts/baseline_metrics.py (which is deliberately zero-AI), this
is the "with AI" comparison point: run both and diff the numbers for your
resume bullet / interview story (report Section 13).

Usage:
    python scripts/run_agent_batch.py --dataset dataset/payments.json
"""

import argparse
import json
import os

from dotenv import load_dotenv

load_dotenv()

from app.classifier import classify_failure
from app.scoring import calculate_recovery_score
from app.tools.recommend_action import recommend_action


def run(dataset_path: str, limit: int = None):
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit(
            "GEMINI_API_KEY not set. Copy backend/.env.example to backend/.env "
            "and add your key before running this script."
        )

    with open(dataset_path) as f:
        records = json.load(f)
    if limit:
        records = records[:limit]

    results = []
    llm_calls = 0

    for r in records:
        classification = classify_failure(r["failure_code"], r["gateway_message"], r["retry_count"])
        score = calculate_recovery_score(classification, r["customer_history"], r["retry_count"])
        decision = recommend_action(
            case_id=r["case_id"],
            recovery_score=score,
            classification=classification,
            amount=r["amount"],
            retry_count=r["retry_count"],
            gateway_message=r["gateway_message"],
            failure_code=r["failure_code"],
            customer_history=r["customer_history"],
        )
        if classification["bucket"] == "ambiguous":
            llm_calls += 1

        results.append({
            "case_id": r["case_id"],
            "bucket": classification["bucket"],
            "true_bucket": r["bucket_label"],
            "action": decision.recommended_action.value,
            "recovery_probability": decision.recovery_probability,
            "reasoning": decision.reasoning,
        })
        print(f"{r['case_id']:<10} [{classification['bucket']:<11}] -> {decision.recommended_action.value:<22} "
              f"(p={decision.recovery_probability:.2f})")

    print(f"\nProcessed {len(results)} cases, {llm_calls} routed to Gemini (ambiguous bucket).")
    print("Full audit trail written to backend/audit_log.jsonl")

    out_path = "agent_batch_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="dataset/payments.json")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N records (useful to test cheaply)")
    args = parser.parse_args()
    run(args.dataset, args.limit)
