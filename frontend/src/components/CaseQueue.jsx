const STATUS_STYLE = {
  pending: { label: 'Pending', className: 'bg-ink-border text-paper' },
  in_review: { label: 'In Review', className: 'bg-brass text-ink' },
  action_taken: { label: 'Action Taken', className: 'bg-brass-soft text-ink' },
  recovered: { label: 'Recovered', className: 'bg-verdigris text-paper' },
  failed: { label: 'Failed', className: 'bg-rust-soft text-ink' },
  do_not_retry: { label: 'Blocked', className: 'bg-rust text-paper' },
}

function StatusChip({ status }) {
  const style = STATUS_STYLE[status] || { label: status, className: 'bg-ink-border text-paper' }
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-sans font-medium ${style.className}`}>
      {style.label}
    </span>
  )
}

function formatINR(amount) {
  return `₹${amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

function CaseCard({ c, onProcess, onApprove, busy }) {
  return (
    <div className="bg-paper rounded-sm p-4 border border-paper-dim flex items-center justify-between gap-4">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-mono text-sm font-semibold text-paper-text">{c.case_id}</span>
          <StatusChip status={c.status} />
          {c.classification_bucket && (
            <span className="font-mono text-[11px] text-paper-text/50">{c.classification_bucket}</span>
          )}
        </div>
        <div className="font-sans text-xs text-paper-text/60">
          {c.failure_code} · retry {c.retry_count} {c.last_action ? `· last action: ${c.last_action}` : ''}
        </div>
      </div>

      <div className="font-mono text-lg font-semibold text-paper-text tabular whitespace-nowrap">
        {formatINR(c.amount)}
      </div>

      <div className="flex gap-2 flex-shrink-0">
        {c.status === 'pending' && (
          <button
            onClick={() => onProcess(c.case_id)}
            disabled={busy}
            className="px-3 py-1.5 rounded-sm bg-ink text-paper font-sans text-xs font-medium hover:bg-ink-light disabled:opacity-40 transition-colors"
          >
            Process
          </button>
        )}
        {c.status === 'in_review' && (
          <button
            onClick={() => onApprove(c.case_id)}
            disabled={busy}
            className="px-3 py-1.5 rounded-sm bg-brass text-ink font-sans text-xs font-medium hover:bg-brass-soft disabled:opacity-40 transition-colors"
          >
            Approve
          </button>
        )}
      </div>
    </div>
  )
}

export default function CaseQueue({ cases, onProcess, onApprove, busyCaseId }) {
  if (!cases) {
    return <div className="font-sans text-sm text-paper/50">Loading cases…</div>
  }
  if (cases.length === 0) {
    return (
      <div className="bg-paper rounded-sm p-8 text-center border border-paper-dim">
        <div className="font-display text-lg text-paper-text mb-1">No cases yet</div>
        <div className="font-sans text-sm text-paper-text/60">
          Run <code className="font-mono">scripts/seed_db.py</code> to load the synthetic dataset.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {cases.map((c) => (
        <CaseCard
          key={c.case_id}
          c={c}
          onProcess={onProcess}
          onApprove={onApprove}
          busy={busyCaseId === c.case_id}
        />
      ))}
    </div>
  )
}
