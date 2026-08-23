# RecoverAI — Pitch Video Script (5 minutes)

Record in one continuous take if you can — a couple of natural pauses read
better to judges than an overly polished, obviously-edited pitch. Screen
record the dashboard and terminal for the demo section; a webcam intro/outro
is optional but helps judges remember a face with the project.

---

## 0:00–1:00 — The problem (60s)

**Say:**
"Every payment gateway loses revenue to failed payments — but not every
failure is the same problem. A card that expired mid-subscription is
completely recoverable. A card reported lost or stolen never should be
retried again. Most recovery systems either retry everything blindly, which
wastes gateway calls and annoys customers, or retry nothing, which leaves
real revenue on the table. I built RecoverAI: an agent that reads *why* a
payment failed, decides the right next action, and only ever takes actions
a human could audit and undo."

**On screen:** title card or you on camera. Keep it to one clear problem
statement — don't list every feature yet.

---

## 1:00–2:30 — Live demo (90s)

**Say (while screen-recording the dashboard):**
"Here's the recovery queue, seeded with a synthetic batch of failed
payments. [Click Process on a clear case.] This one's a straightforward
expired card — the deterministic rules resolve it instantly, no AI call
needed, and it fires a retry through Razorpay's test-mode API. [Click
Process on an ambiguous case.] This one has a vague gateway message — this
is the ~30% of cases that actually need judgment, so it goes to Gemini,
which returns a structured recovery probability, not free text. [Click
Process on a high-value case, show it land in 'In Review'.] And this one's
above the approval threshold, so instead of acting automatically, it waits
for a human — I approve it here. [Point at the pipeline bar and metrics
panel.] Everything you see updating live is real state from the backend —
recovery rate, recovered revenue, and this false-positive-cost number,
which should always read zero: it's the canary that tells us if a
guardrail ever failed to block a case that shouldn't be retried."

**On screen:** the actual dashboard, doing the actual actions. Don't
narrate over a static screenshot — click through it live.

---

## 2:30–4:00 — Architecture and guardrails (90s)

**Say:**
"The core design decision is: the model recommends, deterministic code
authorizes and executes. [Show the architecture diagram from the README.]
A failure comes in, gets classified by rules first — clear, edge, or
adversarial cases never touch the LLM at all. Only genuinely ambiguous
cases go to Gemini, and even then, Gemini only ever returns a constrained
JSON schema — never free text that gets treated as an action. Every single
decision, whether it came from the rules or from Gemini, passes through
one policy engine before anything executes. That's what enforces the hard
retry cap, the cooldown window, the do-not-retry list for terminal
failures, and the high-value approval step. [Show a snippet of the
guardrail test — the one that mocks an overconfident LLM.] I specifically
tested what happens if the model recommends something wrong — here, I
mock an LLM decision that ignores the retry cap, and the policy engine
catches and overrides it. On a baseline run against 100 synthetic cases,
the deterministic rules alone hit 100% classification agreement with
ground truth, and zero guardrail failures — that's the floor the AI layer
has to add value on top of, not replace."

**On screen:** architecture diagram, then a quick cut to the test file and
terminal output showing tests passing.

---

## 4:00–5:00 — Roadmap and close (60s)

**Say:**
"The honest limitation right now is the dataset — it's synthetic, so the
100% agreement number tells you the rules are internally consistent, not
that they'll generalize to messier real-world gateway messages. The next
step is running this against real Razorpay test-mode failure logs and
seeing where the rule set actually breaks. Longer term: multi-currency
support, per-merchant configurable thresholds, and a live A/B against the
deterministic-only baseline to get a real recovery-rate lift number instead
of a synthetic one. But the core idea — model recommends, code decides —
is the part I'd keep regardless of what dataset or gateway sits underneath
it. Thanks for watching."

**On screen:** roadmap section of the README, then back to you or a closing
title card with the repo link.

---

## Recording checklist

- [ ] Dashboard running locally with `npm run dev`, backend running with
      `uvicorn app.main:app --reload`, and the DB freshly seeded so the
      pipeline bar has a realistic spread of statuses to show
- [ ] At least one `pending`, one `in_review`, and a few `recovered`/`do_not_retry`
      cases visible before you start recording, so the pipeline bar isn't empty
- [ ] Terminal window ready with `pytest tests/ -v` output pre-run (or run
      it live if you're confident it'll pass cleanly)
- [ ] Screen resolution set so text is readable at 1080p export
- [ ] Practice the timing once — 5 minutes goes fast once you're clicking
      through a live demo
