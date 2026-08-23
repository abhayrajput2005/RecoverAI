const SOURCE_COLOR = {
  deterministic: 'text-verdigris-soft',
  llm: 'text-brass-soft',
  policy_override: 'text-rust-soft',
  execution: 'text-paper/70',
  webhook: 'text-paper/50',
}

export default function AuditTrail({ entries }) {
  if (!entries) {
    return <div className="font-sans text-sm text-paper/50">Loading audit log…</div>
  }

  const recent = [...entries].reverse().slice(0, 40)

  return (
    <div>
      <h2 className="font-display text-2xl text-paper mb-3">Audit Trail</h2>
      <div className="bg-ink-light border border-ink-border rounded-sm p-4 h-96 overflow-y-auto font-mono text-xs space-y-1.5">
        {recent.length === 0 && <div className="text-paper/40">No events logged yet.</div>}
        {recent.map((entry, i) => (
          <div key={i} className="flex gap-2 leading-relaxed">
            <span className="text-paper/30 whitespace-nowrap">
              {new Date(entry.timestamp).toLocaleTimeString('en-IN', { hour12: false })}
            </span>
            <span className={`${SOURCE_COLOR[entry.source] || 'text-paper/60'} whitespace-nowrap`}>
              [{entry.source}]
            </span>
            <span className="text-paper/40 whitespace-nowrap">{entry.case_id}</span>
            <span className="text-paper/70 truncate">{JSON.stringify(entry.payload)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
