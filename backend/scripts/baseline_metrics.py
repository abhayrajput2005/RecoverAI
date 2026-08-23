"""
Day 2-3 deliverable: baseline metrics with zero AI (report Section 8 / Day
2-3 phase description).

Runs the deterministic classifier + scoring + policy engine over the full
synthetic dataset and reports:
  - classification agreement with the dataset's ground-truth bucket_label
  - action distribution
  - guardrail effectiveness: adversarial cases must ALWAYS resolve to
    do_not_retry (false-positive cost proxy)
  - average recovery_score per bucket

This is the number the Day 4-6 LLM agent layer has to beat, and it's also
the "held-out evaluation" exception list mentioned in report Section 12/13.

Usage:
    python scripts/baseline_metrics.py --dataset dataset/payments.json
"""

import argparse
import json
from collections import defaultdict

from app.classifier import classify_failure
from app.policy import decide_action
from app.scoring import calculate_recovery_score


def run(dataset_path: str):
    with open(dataset_path) as f:
        records = json.load(f)

    agreement = 0
    total = len(records)
    action_counts = defaultdict(int)
    score_sums = defaultdict(float)
    score_counts = defaultdict(int)
    false_positives = []  # adversarial cases that did NOT get do_not_retry
    exceptions = []       # bucket disagreements, for the held-out exception list

    for r in records:
        classification = classify_failure(r["failure_code"], r["gateway_message"], r["retry_count"])
        score = calculate_recovery_score(classification, r["customer_history"], r["retry_count"])
        decision = decide_action(
            r["case_id"], classification, score, r["amount"], r["retry_count"]
        )

        predicted_bucket = classification["bucket"]
        true_bucket = r["bucket_label"]

        if predicted_bucket == true_bucket:
            agreement += 1
        else:
            exceptions.append({
                "case_id": r["case_id"],
                "failure_code": r["failure_code"],
                "true_bucket": true_bucket,
                "predicted_bucket": predicted_bucket,
            })

        action_counts[decision.recommended_action.value] += 1
        score_sums[predicted_bucket] += score
        score_counts[predicted_bucket] += 1

        if true_bucket == "adversarial" and decision.recommended_action.value != "do_not_retry":
            false_positives.append({
                "case_id": r["case_id"],
                "amount": r["amount"],
                "action_taken": decision.recommended_action.value,
            })

    print("=== RecoverAI — Deterministic Core Baseline Metrics (zero AI) ===\n")
    print(f"Total cases evaluated:        {total}")
    print(f"Classification agreement:     {agreement}/{total} ({agreement/total:.1%})")
    print(f"  (Note: 'ambiguous' cases are EXPECTED to need LLM judgment —\n"
          f"   Day 2-3 rules deliberately don't try to resolve them further.)\n")

    print("Action distribution:")
    for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
        print(f"  {action:<22} {count:>4}  ({count/total:.1%})")

    print("\nAverage recovery_score by predicted bucket:")
    for bucket, s in score_sums.items():
        print(f"  {bucket:<12} {s/score_counts[bucket]:.3f}  (n={score_counts[bucket]})")

    print(f"\nGuardrail check — adversarial cases NOT routed to do_not_retry: {len(false_positives)}")
    if false_positives:
        print("  !! GUARDRAIL FAILURE — this must be 0. Details:")
        for fp in false_positives:
            print(f"     {fp}")
    else:
        print("  PASS — every adversarial/terminal case was correctly blocked.")

    if exceptions:
        print(f"\nHeld-out exception list ({len(exceptions)} bucket disagreements) — "
              f"expected mostly on the 'ambiguous' bucket:")
        for e in exceptions[:10]:
            print(f"  {e}")
        if len(exceptions) > 10:
            print(f"  ... and {len(exceptions) - 10} more")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="dataset/payments.json")
    args = parser.parse_args()
    run(args.dataset)
