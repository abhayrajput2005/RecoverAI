import {
  RETRY_CAP,
  classifySource,
  formatAction,
  formatINR,
  formatWhen,
  latestDecision,
  latestPolicy,
  latestWebhook,
  outcomeLabel,
  policyVerdict,
  statusLabel,
  storySteps,
} from '../lib'

function Row({ label, children }) {
  return (
    <div className="grid grid-cols-[7.5rem_1fr] gap-2 py-1.5 border-b border-ink-border/80">
      <dt className="font-sans text-[11px] uppercase tracking-wide text-paper/40">{label}</dt>
      <dd className="font-mono text-sm text-paper break-words">{children}</dd>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <section className="mb-5">
      <h3 className="font-sans text-[11px] uppercase tracking-[0.14em] text-brass mb-2">{title}</h3>
      <dl>{children}</dl>
    </section>
  )
}

function Story({ caseRecord }) {
  const steps = storySteps(caseRecord)
  return (
    <ol className="mb-5 grid grid-cols-1 gap-1.5" aria-label="Case decision path">
      {steps.map((step, i) => (
        <li key={step.key} className="flex items-start gap-2">
          <span
            className={`mt-0.5 h-2 w-2 rounded-full flex-shrink-0 ${step.done ? 'bg-brass' : 'bg-ink-border'}`}
            aria-hidden
          />
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-sans text-[10px] uppercase tracking-wide text-paper/45">
                {i + 1}. {step.label}
              </span>
              <span className="font-mono text-[11px] text-paper/70 truncate">{step.note}</span>
            </div>
          </div>
        </li>
      ))}
    </ol>
  )
}

export default function CaseDetail({ caseRecord, auditEntries, onClose, onProcess, onApprove, busy }) {
  if (!caseRecord) return null

  const c = caseRecord
  const decision = latestDecision(auditEntries, c.case_id)
  const policy = latestPolicy(auditEntries, c.case_id)
  const webhook = latestWebhook(auditEntries, c.case_id)
  const trail = (auditEntries || []).filter((e) => e.case_id === c.case_id)
  const atCap = (c.retry_count || 0) >= RETRY_CAP
  const adversarial = c.classification_bucket === 'adversarial' || c.failure_code === 'FRAUD_FLAG'
  const score = decision?.payload?.recovery_probability ?? policy?.payload?.recovery_probability
  const recommended = decision?.payload?.recommended_action || policy?.payload?.recommended_action || c.last_action
  const outcomeAt = webhook?.timestamp || (c.status === 'recovered' || c.status === 'failed' ? c.last_action_at : null)

  return (
    <aside
      className="drawer-enter rounded-sm border border-ink-border bg-ink-light p-4 md:p-5 h-full overflow-y-auto scroll-thin"
      aria-label={`Case ${c.case_id} details`}
    >
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="font-mono text-xs text-paper/40">Case</div>
          <h2 className="font-display text-2xl text-paper">{c.case_id}</h2>
          <p className="font-sans text-sm text-paper/60 mt-1">
            {statusLabel(c.status)} · {formatINR(c.amount, { digits: 2 })} {c.currency || 'INR'}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="font-sans text-xs text-paper/50 hover:text-paper px-2 py-1"
          aria-label="Close case details"
        >
          Close
        </button>
      </div>

      <Story caseRecord={c} />

      {adversarial && (
        <div className="mb-4 rounded-sm border border-rust/50 bg-rust/10 px-3 py-2 font-sans text-xs text-paper/80">
          {c.failure_code || 'FRAUD_FLAG'} → adversarial → <strong>BLOCKED</strong> → no Razorpay execution.
        </div>
      )}
      {c.status === 'recovered' && (
        <div className="mb-4 rounded-sm border border-verdigris/50 px-3 py-2 font-sans text-xs text-paper/80">
          {c.failure_code} → {c.classification_bucket || 'classified'} → {formatAction(c.last_action)} → Razorpay TEST
          → Recovered {c.recovered_amount != null ? formatINR(c.recovered_amount, { digits: 2 }) : ''}.
        </div>
      )}
      {atCap && c.status === 'pending' && (
        <div className="mb-4 rounded-sm border border-brass/40 bg-brass/10 px-3 py-2 font-sans text-xs text-paper/80">
          Retry count is at the policy cap ({RETRY_CAP}). Process still goes through the backend; the UI cannot override it.
        </div>
      )}
      {c.status === 'action_taken' && (
        <div className="mb-4 rounded-sm border border-brass/40 px-3 py-2 font-sans text-xs text-paper/80">
          Recovery action executed. Awaiting payment outcome via webhook — not counted as recovered yet.
        </div>
      )}

      <div className="flex flex-wrap gap-2 mb-5">
        {c.status === 'pending' && (
          <button
            type="button"
            disabled={busy}
            onClick={() => onProcess(c.case_id)}
            className="px-3 py-1.5 rounded-sm bg-brass text-ink font-sans text-xs font-medium disabled:opacity-40"
          >
            {busy ? 'Processing…' : 'Process'}
          </button>
        )}
        {c.status === 'in_review' && (
          <button
            type="button"
            disabled={busy}
            onClick={() => onApprove(c.case_id)}
            className="px-3 py-1.5 rounded-sm bg-brass text-ink font-sans text-xs font-medium disabled:opacity-40"
          >
            {busy ? 'Approving…' : 'Approve'}
          </button>
        )}
        {c.status === 'action_taken' && (
          <span className="px-3 py-1.5 rounded-sm border border-brass/40 font-sans text-xs text-brass-soft">
            Awaiting payment outcome
          </span>
        )}
        {c.status === 'recovered' && (
          <span className="px-3 py-1.5 rounded-sm border border-verdigris/40 font-sans text-xs text-verdigris-soft">
            Recovered
          </span>
        )}
        {c.status === 'do_not_retry' && (
          <span className="px-3 py-1.5 rounded-sm border border-rust/40 font-sans text-xs text-rust-soft">Blocked</span>
        )}
        {c.status === 'failed' && (
          <span className="px-3 py-1.5 rounded-sm border border-rust/40 font-sans text-xs text-rust-soft">Failed</span>
        )}
      </div>

      <Section title="Transaction">
        <Row label="Case ID">{c.case_id}</Row>
        <Row label="Payment ID">{c.payment_id || '—'}</Row>
        <Row label="Amount">{formatINR(c.amount, { digits: 2 })}</Row>
        <Row label="Currency">{c.currency || 'INR'}</Row>
        <Row label="Method">{c.payment_method || '—'}</Row>
        <Row label="Failure">{c.failure_code || '—'}</Row>
        <Row label="Gateway">{c.gateway_message || '—'}</Row>
        <Row label="Failed at">{formatWhen(c.failed_at)}</Row>
      </Section>

      <Section title="Customer">
        <Row label="Successful 90d">{c.successful_payments_last_90d ?? '—'}</Row>
        <Row label="Failed 90d">{c.failed_payments_last_90d ?? '—'}</Row>
        <Row label="Subscription">{c.is_subscription ? 'Yes' : 'No'}</Row>
        <Row label="Customer">{c.customer_id || '—'}</Row>
      </Section>

      <Section title="Recovery analysis">
        <Row label="Classification">{c.classification_bucket || '—'}</Row>
        <Row label="Source">{classifySource(c.classification_bucket)}</Row>
        <Row label="Score">{score != null ? score : 'Available after process (from audit)'}</Row>
        <Row label="Recommended">{formatAction(recommended)}</Row>
        <Row label="Policy">{policyVerdict(c, policy || decision)}</Row>
        <Row label="Reasoning">{decision?.payload?.reasoning || policy?.payload?.reasoning || '—'}</Row>
      </Section>

      <Section title="Execution">
        <Row label="Last action">{formatAction(c.last_action)}</Row>
        <Row label="Retry count">{`${c.retry_count ?? 0} / ${RETRY_CAP}`}</Row>
        <Row label="Razorpay ref">
          {c.razorpay_reference_id
            ? c.razorpay_reference_id
            : c.last_action
              ? 'Not stored on case — see last action / audit'
              : 'none — no execution'}
        </Row>
        <Row label="Executed at">{formatWhen(c.last_action_at)}</Row>
        <Row label="Status">{statusLabel(c.status)}</Row>
      </Section>

      <Section title="Outcome">
        <Row label="Status">{outcomeLabel(c)}</Row>
        <Row label="Recovered">
          {c.status === 'recovered' && c.recovered_amount != null
            ? formatINR(c.recovered_amount, { digits: 2 })
            : 'Not recovered'}
        </Row>
        <Row label="Timestamp">{formatWhen(outcomeAt)}</Row>
      </Section>

      <Section title="Audit history">
        {trail.length === 0 && <p className="font-sans text-xs text-paper/40">No audit events for this case yet.</p>}
        <ul className="space-y-2">
          {trail.map((e, i) => (
            <li key={`${e.timestamp}-${i}`} className="font-mono text-[11px] text-paper/70">
              <span className="text-paper/35">{formatWhen(e.timestamp)}</span>{' '}
              <span className="text-brass-soft">{e.source}</span>{' '}
              {e.payload?.recommended_action || e.payload?.action || e.payload?.event || e.payload?.blocked || ''}
            </li>
          ))}
        </ul>
      </Section>
    </aside>
  )
}
