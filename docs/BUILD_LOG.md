# RecoverAI — Development Build Log

This is the day-by-day build history. For the case-study writeup, see the
[top-level README](../README.md).

## Status: Day 10 of 12

- [x] Repo scaffolded (backend/frontend split)
- [x] Synthetic dataset generator (`backend/dataset/generate_dataset.py`)
- [x] Data models (`backend/app/models.py`)
- [x] 8-tool interface stubbed (`backend/app/tools/`)
- [x] FastAPI skeleton (`backend/app/main.py`)
- [x] Deterministic classifier + scorer + policy engine (Day 2-3)
- [x] Test suite for the deterministic core — 13 tests (Day 2-3)
- [x] Baseline metrics script (Day 2-3) — see results below
- [x] Gemini agent layer for ambiguous-case judgment (Day 4-6)
- [x] Full decision audit trail (`app/audit.py`)
- [x] Routing + guardrail-override tests — 4 more tests (Day 4-6)
- [x] SQLite persistence layer (`app/db.py`, `scripts/seed_db.py`) (Day 7-8)
- [x] Razorpay test-mode Orders + Payment Links (`app/razorpay_client.py`) (Day 7-8)
- [x] Idempotency + cooldown guardrails on execution, tested — 6 more tests (Day 7-8)
- [x] Webhook endpoint for payment status updates (Day 7-8)
- [x] Full per-case pipeline (`app/pipeline.py`) — classify/score/decide/act (Day 9)
- [x] Simulated approval flow for high-value cases (`POST /cases/{id}/approve`) (Day 9)
- [x] Live metrics endpoint (`app/metrics.py`, `GET /metrics`) (Day 9)
- [x] Metrics + approval tests — 5 more tests (Day 9)
- [x] React dashboard — pipeline view, case queue, live metrics, audit trail (Day 10)
- [x] Deployment configs for Render (backend) + Vercel (frontend) (Day 10)
- [ ] Case-study README rewrite + pitch video (Day 11)

### AI provider

This build uses **Google Gemini** (`google-genai` SDK) for the LLM agent
layer instead of the Claude API originally listed in the report's tech
stack — same design principle applies: the model only ever produces a
structured `AgentDecision` for the `ambiguous` bucket, and every output
still passes through `app.policy.authorize()` before it's treated as
executable.

### Baseline results (zero AI, n=100 synthetic cases, seed=42)

```
Classification agreement with ground truth: 100/100 (100%)
Guardrail check — adversarial cases NOT blocked: 0  (PASS)

Action distribution:
  immediate_retry        33
  do_not_retry            30
  payment_link            17
  alternative_method      16
  escalate_human_review    4
```

This is the number the Gemini agent layer needs to match or beat on the
`ambiguous` bucket specifically (30/100 cases) — the deterministic core
already resolves `clear`, `edge`, and `adversarial` cases correctly with
zero AI involved. Run `scripts/run_agent_batch.py` (once your API key is
set up) to get the "with AI" comparison numbers.

## Project structure

```
RecoverAI/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entrypoint + webhook + endpoints
│   │   ├── models.py        # RecoveryCase, AgentDecision, CaseOutcome, etc.
│   │   ├── rules.py         # guardrail constants
│   │   ├── classifier.py    # deterministic failure classifier
│   │   ├── scoring.py       # deterministic recovery-score formula
│   │   ├── policy.py        # decision + guardrail authorization
│   │   ├── agent.py         # Gemini agent (ambiguous cases only)
│   │   ├── pipeline.py      # per-case orchestration + approval flow
│   │   ├── metrics.py       # live recovery-rate / accuracy metrics
│   │   ├── db.py            # SQLite persistence
│   │   ├── audit.py         # decision audit trail
│   │   ├── razorpay_client.py
│   │   └── tools/           # the 8 agent tools (report Section 4)
│   ├── dataset/
│   │   └── generate_dataset.py
│   ├── scripts/
│   │   ├── seed_db.py
│   │   ├── baseline_metrics.py
│   │   └── run_agent_batch.py
│   ├── tests/
│   └── requirements.txt
├── frontend/                 # React + Vite + Tailwind dashboard
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/       # Pipeline, CaseQueue, MetricsPanel, AuditTrail
│   └── package.json
└── render.yaml               # backend deployment config
```

## Getting started (backend)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# set up your API keys
cp .env.example .env
# edit .env: add your Gemini key (console.cloud.google.com / Google AI Studio)
# and your Razorpay TEST MODE keys (dashboard.razorpay.com -> Settings -> API Keys)

# generate the synthetic dataset and load it into the DB
python dataset/generate_dataset.py --count 100 --seed 42 --out dataset/payments.json
python scripts/seed_db.py --dataset dataset/payments.json

# run the API
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/health` to confirm it's running, and
`http://localhost:8000/cases` to see the seeded recovery queue.

### Exposing webhooks locally

Razorpay needs a public URL to send webhook events to. For local dev, use
a tunnel (e.g. `ngrok http 8000`) and register `https://<your-tunnel>/webhooks/razorpay`
in the Razorpay dashboard under Settings -> Webhooks, subscribed to
`payment.captured`, `payment.failed`, and `payment_link.paid`.

### Run the tests

```bash
pytest tests/ -v
```

### Run the baseline metrics (zero AI)

```bash
python scripts/baseline_metrics.py --dataset dataset/payments.json
```

### Run the full agent batch (needs GEMINI_API_KEY)

```bash
python scripts/run_agent_batch.py --dataset dataset/payments.json --limit 10  # cheap test run first
```

### Process cases through the live API

```bash
# Run the full loop for one case
curl -X POST http://localhost:8000/cases/RC-1000/process

# If it comes back status='in_review' (high-value case), approve it:
curl -X POST http://localhost:8000/cases/RC-1000/approve

# Check the live metrics
curl http://localhost:8000/metrics
```

## Getting started (frontend)

```bash
cd frontend
npm install
cp .env.example .env  # defaults to http://localhost:8000, fine for local dev
npm run dev
```

Visit `http://localhost:5173`. The dashboard polls `/cases`, `/metrics`,
and `/audit-log` every 8 seconds, and lets you trigger `/process` and
`/approve` directly from the case queue.

### Design notes

The dashboard uses a "Recovery Ledger" visual language: a dark operations
shell holding warm paper-colored case cards (like a physical ledger book on
a steel desk), with a terminal-style dark audit log — the recovery agent
keeps a ledger of cases but logs raw system events like a terminal. The
signature element is the horizontal pipeline bar at the top: it's not
decorative, it's the actual live funnel of cases across every status.

## Deployment

**Backend (Render):**
1. Push this repo to GitHub.
2. In Render, "New +" -> "Blueprint", point it at the repo — `render.yaml`
   at the root configures the service automatically.
3. In the Render dashboard, set the secret env vars: `GEMINI_API_KEY`,
   `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`.
4. Once deployed, register the webhook URL (`https://<your-render-url>/webhooks/razorpay`)
   in the Razorpay dashboard.

**Frontend (Vercel):**
1. Import the repo in Vercel, set the root directory to `frontend`.
2. Set the env var `VITE_API_URL` to your deployed Render backend URL.
3. Deploy — `vercel.json` configures the Vite build automatically.

Both platforms have generous free tiers, which is enough for a buildathon
demo (report Section 6: deployment doesn't need to be production-grade,
just reachable via a public URL).

## Design principle

The model recommends, deterministic application logic authorizes and
executes. The LLM never directly performs an unconstrained financial action —
every `recommend_action()` output is validated against the guardrails
(retry caps, cooldowns, do-not-retry list) before any Razorpay API call fires.

## Guardrails (non-negotiable)

- Hard cap on retry attempts per payment (max 3), enforced in code.
- Cooldown window between retries (6–12 hours minimum).
- No action above a configurable ₹ threshold without simulated approval.
- Explicit do-not-retry list for terminal failures (lost/stolen card, closed
  account, fraud flag).
- Every LLM decision returns a structured object — never free text taken as
  an executable action.
