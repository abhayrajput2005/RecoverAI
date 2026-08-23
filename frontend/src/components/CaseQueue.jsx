import { FILTERS, RETRY_CAP, formatAction, formatINR, sortCases, statusLabel } from '../lib'

const TONE = {
  pending: 'bg-ink-border text-paper',
  ready: 'bg-ink-border text-paper',
  in_review: 'bg-brass text-ink',
  action_taken: 'bg-brass-soft text-ink',
  recovered: 'bg-verdigris text-paper',
  failed: 'bg-rust-soft text-ink',
  do_not_retry: 'bg-rust text-paper',
}

const BAR = {
  pending: 'bg-ink-border',
  ready: 'bg-ink-border',
  in_review: 'bg-brass',
  action_taken: 'bg-brass-soft',
  recovered: 'bg-verdigris',
  failed: 'bg-rust-soft',
  do_not_retry: 'bg-rust',
}

function StatusChip({ status }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-sans font-medium ${TONE[status] || TONE.pending}`}>
      {statusLabel(status)}
    </span>
  )
}

function CaseCard({ c, selected, busy, locked, onSelect, onProcess, onApprove }) {
  const atCap = (c.retry_count || 0) >= RETRY_CAP
  const processLabel = busy ? 'Processing…' : 'Process'
  const approveLabel = busy ? 'Approving…' : 'Approve'

  return (
    <article
      className={`bg-paper rounded-sm border flex overflow-hidden ${
        selected ? 'border-brass ring-1 ring-brass' : 'border-paper-dim'
      }`}
    >
      <div className={`w-1.5 flex-shrink-0 ${BAR[c.status] || BAR.pending}`} aria-hidden />
      <div className="flex-1 min-w-0 p-3 sm:p-4">
        <button
          type="button"
          onClick={() => onSelect(c.case_id)}
          className="w-full text-left"
          aria-pressed={selected}
          aria-label={`Open details for ${c.case_id}`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-sm font-semibold text-paper-text">{c.case_id}</span>
                <StatusChip status={c.status} />
                {c.classification_bucket && (
                  <span className="font-mono text-[11px] text-paper-text/50">{c.classification_bucket}</span>
                )}
              </div>
              <div className="mt-1 font-sans text-xs text-paper-text/60 truncate">
                {c.failure_code}
                {c.payment_method ? ` · ${c.payment_method}` : ''}
                {c.last_action ? ` · last: ${formatAction(c.last_action)}` : ''}
              </div>
              <div className="mt-1 flex flex-wrap gap-x-3 font-mono text-[11px] text-paper-text/45">
                <span>Retry {c.retry_count ?? 0}/{RETRY_CAP}</span>
                {atCap && <span className="text-rust">retry cap</span>}
                {c.recovered_amount != null && <span className="text-verdigris">recovered {formatINR(c.recovered_amount, { digits: 2 })}</span>}
              </div>
            </div>
            <div className="font-mono text-lg font-semibold text-paper-text tabular whitespace-nowrap">
              {formatINR(c.amount)}
            </div>
          </div>
        </button>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          {c.status === 'pending' && (
            <button
              type="button"
              onClick={() => onProcess(c.case_id)}
              disabled={busy || locked}
              aria-label={`${processLabel} ${c.case_id}`}
              className="px-3 py-1.5 rounded-sm bg-ink text-paper font-sans text-xs font-medium hover:bg-ink-light disabled:opacity-40 disabled:pointer-events-none transition-colors"
            >
              {processLabel}
            </button>
          )}
          {c.status === 'in_review' && (
            <button
              type="button"
              onClick={() => onApprove(c.case_id)}
              disabled={busy || locked}
              aria-label={`${approveLabel} ${c.case_id}`}
              className="px-3 py-1.5 rounded-sm bg-brass text-ink font-sans text-xs font-medium hover:bg-brass-soft disabled:opacity-40 disabled:pointer-events-none transition-colors"
            >
              {approveLabel}
            </button>
          )}
          {c.status === 'action_taken' && (
            <span className="px-2 py-1 font-sans text-[11px] text-paper-text/60">Awaiting payment outcome</span>
          )}
          {c.status === 'recovered' && (
            <span className="px-2 py-1 font-sans text-[11px] text-verdigris">Recovered</span>
          )}
          {c.status === 'do_not_retry' && (
            <span className="px-2 py-1 font-sans text-[11px] text-rust">Blocked</span>
          )}
          {c.status === 'failed' && (
            <span className="px-2 py-1 font-sans text-[11px] text-rust">Failed</span>
          )}
          <button
            type="button"
            onClick={() => onSelect(c.case_id)}
            className="px-3 py-1.5 rounded-sm border border-paper-dim text-paper-text font-sans text-xs hover:bg-paper-dim"
          >
            Details
          </button>
        </div>
      </div>
    </article>
  )
}

export default function CaseQueue({
  cases,
  filter,
  query,
  onFilter,
  onQuery,
  selectedId,
  onSelect,
  onProcess,
  onApprove,
  busyCaseId,
}) {
  if (!cases) {
    return <div className="font-sans text-sm text-paper/50">Loading cases…</div>
  }
  if (cases.length === 0) {
    return (
      <div className="bg-paper rounded-sm p-8 text-center border border-paper-dim">
        <div className="font-display text-lg text-paper-text mb-1">No cases yet</div>
        <div className="font-sans text-sm text-paper-text/60">
          Run <code className="font-mono">scripts/seed_db.py</code> to load the dataset.
        </div>
      </div>
    )
  }

  const q = query.trim().toLowerCase()
  const filtered = sortCases(cases).filter((c) => {
    if (filter !== 'all' && c.status !== filter) return false
    if (!q) return true
    return [c.case_id, c.failure_code, c.last_action, c.classification_bucket, c.payment_id]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q))
  })

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-3">
        <label className="sr-only" htmlFor="case-search">
          Search cases
        </label>
        <input
          id="case-search"
          value={query}
          onChange={(e) => onQuery(e.target.value)}
          placeholder="Search ID, failure code…"
          className="flex-1 min-w-0 rounded-sm border border-ink-border bg-ink-light px-3 py-2 font-mono text-sm text-paper placeholder:text-paper/30"
        />
        <div className="flex flex-wrap gap-1" role="tablist" aria-label="Filter by status">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              type="button"
              role="tab"
              aria-selected={filter === f.key}
              onClick={() => onFilter(f.key)}
              className={`px-2.5 py-1 rounded-sm font-sans text-[11px] ${
                filter === f.key ? 'bg-brass text-ink' : 'bg-ink-light text-paper/70 border border-ink-border'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <p className="font-sans text-xs text-paper/40 mb-2">
        Showing {filtered.length} of {cases.length}
      </p>

      <div className="space-y-2 max-h-[70vh] overflow-y-auto scroll-thin pr-1">
        {filtered.length === 0 && (
          <div className="font-sans text-sm text-paper/50 py-8 text-center">No cases match this filter.</div>
        )}
        {filtered.map((c) => (
          <CaseCard
            key={c.case_id}
            c={c}
            selected={selectedId === c.case_id}
            busy={busyCaseId === c.case_id}
            locked={Boolean(busyCaseId)}
            onSelect={onSelect}
            onProcess={onProcess}
            onApprove={onApprove}
          />
        ))}
      </div>
    </div>
  )
}
