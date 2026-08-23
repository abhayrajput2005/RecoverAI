const STAGES = [
  { key: 'pending', label: 'Pending', color: 'bg-ink-border', text: 'text-paper/70' },
  { key: 'in_review', label: 'In Review', color: 'bg-brass', text: 'text-ink' },
  { key: 'action_taken', label: 'Action Taken', color: 'bg-brass-soft', text: 'text-ink' },
  { key: 'recovered', label: 'Recovered', color: 'bg-verdigris', text: 'text-paper' },
  { key: 'failed', label: 'Failed', color: 'bg-rust-soft', text: 'text-ink' },
  { key: 'do_not_retry', label: 'Blocked', color: 'bg-rust', text: 'text-paper' },
]

export default function Pipeline({ statusBreakdown = {}, totalCases = 0 }) {
  const total = totalCases || 1

  return (
    <div className="mb-10">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="font-display text-2xl text-paper">Recovery Pipeline</h2>
        <span className="font-mono text-xs text-paper/50 tabular">{totalCases} cases tracked</span>
      </div>
      <div className="flex w-full h-16 rounded-sm overflow-hidden border border-ink-border">
        {STAGES.map((stage) => {
          const count = statusBreakdown[stage.key] || 0
          const pct = (count / total) * 100
          if (count === 0) return null
          return (
            <div
              key={stage.key}
              className={`${stage.color} ${stage.text} flex flex-col items-center justify-center transition-all`}
              style={{ width: `${pct}%`, minWidth: count > 0 ? '48px' : '0' }}
              title={`${stage.label}: ${count}`}
            >
              <span className="font-mono text-sm font-semibold tabular">{count}</span>
            </div>
          )
        })}
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2">
        {STAGES.map((stage) => (
          <div key={stage.key} className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${stage.color}`} />
            <span className="font-sans text-xs text-paper/60">{stage.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
