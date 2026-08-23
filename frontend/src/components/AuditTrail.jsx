const SOURCE_META = {
  deterministic: { label: 'Classifier', className: 'text-verdigris-soft' },
  llm: { label: 'Gemini', className: 'text-brass-soft' },
  policy_override: { label: 'Policy', className: 'text-rust-soft' },
  execution: { label: 'Execute', className: 'text-paper/70' },
  webhook: { label: 'Webhook', className: 'text-paper/50' },
}

function summarize(entry) {
  const p = entry.payload || {}
  if (p.recommended_action) {
    return `${p.recommended_action}${p.recovery_probability != null ? ` · score ${p.recovery_probability}` : ''}`
  }
  if (p.executed === true) return `executed ${p.action || ''} ${p.razorpay_reference_id || ''}`.trim()
  if (p.executed === false) return 'not executed'
  if (p.blocked) return `blocked: ${p.blocked}`
  if (p.event) return p.event
  if (p.approved) return 'human approved'
  try {
    return JSON.stringify(p)
  } catch {
    return ''
  }
}

export default function AuditTrail({ entries, highlightCaseId, onSelectCase }) {
  if (!entries) {
    return <div className="font-sans text-sm text-paper/50">Loading audit log…</div>
  }

  const recent = [...entries].reverse().slice(0, 60)

  return (
    <div>
      <h2 className="font-display text-xl text-paper mb-3">Audit trail</h2>
      <div className="bg-ink-light border border-ink-border rounded-sm p-3 h-80 overflow-y-auto scroll-thin font-mono text-xs space-y-1">
        {recent.length === 0 && <div className="text-paper/40 font-sans">No events logged yet.</div>}
        {recent.map((entry, i) => {
          const meta = SOURCE_META[entry.source] || { label: entry.source, className: 'text-paper/60' }
          const active = highlightCaseId && entry.case_id === highlightCaseId
          return (
            <button
              type="button"
              key={`${entry.timestamp}-${i}`}
              onClick={() => onSelectCase?.(entry.case_id)}
              className={`w-full text-left flex flex-wrap gap-x-2 gap-y-0.5 leading-relaxed rounded-sm px-1 py-0.5 hover:bg-ink ${active ? 'bg-ink' : ''}`}
            >
              <span className="text-paper/30 whitespace-nowrap">
                {new Date(entry.timestamp).toLocaleTimeString('en-IN', { hour12: false })}
              </span>
              <span className={`${meta.className} whitespace-nowrap`}>[{meta.label}]</span>
              <span className="text-brass-soft/80 whitespace-nowrap">{entry.case_id}</span>
              <span className="text-paper/70 truncate">{summarize(entry)}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
