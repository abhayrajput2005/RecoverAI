import { formatINR, formatPct } from '../lib'

const PIPELINE = [
  { id: 'analyze', label: 'Analysis' },
  { id: 'recommend', label: 'Recommendation' },
  { id: 'policy', label: 'Policy' },
  { id: 'action', label: 'Razorpay action' },
  { id: 'outcome', label: 'Payment outcome' },
]

const STAGES = [
  { key: 'pending', label: 'Pending', swatch: 'bg-ink-border' },
  { key: 'in_review', label: 'In Review', swatch: 'bg-brass' },
  { key: 'action_taken', label: 'Action Taken', swatch: 'bg-brass-soft' },
  { key: 'recovered', label: 'Recovered', swatch: 'bg-verdigris' },
  { key: 'failed', label: 'Failed', swatch: 'bg-rust-soft' },
  { key: 'do_not_retry', label: 'Blocked', swatch: 'bg-rust' },
]

export default function Pipeline({ statusBreakdown = {}, totalCases = 0, onFilter }) {
  const total = totalCases || 1

  return (
    <section className="mb-8" aria-labelledby="pipeline-heading">
      <div className="flex items-baseline justify-between gap-4 mb-4">
        <h2 id="pipeline-heading" className="font-display text-2xl text-paper">
          Recovery pipeline
        </h2>
        <span className="font-mono text-xs text-paper/50 tabular">{totalCases} cases tracked</span>
      </div>

      <ol className="flex flex-wrap items-center gap-2 mb-5">
        {PIPELINE.map((step, i) => (
          <li key={step.id} className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-sm border border-ink-border bg-ink-light px-2.5 py-1 font-sans text-[11px] uppercase tracking-wide text-paper/80">
              {step.label}
            </span>
            {i < PIPELINE.length - 1 && (
              <span className="text-brass/70 font-mono text-xs hidden sm:inline" aria-hidden>
                →
              </span>
            )}
          </li>
        ))}
      </ol>

      <div
        className="flex w-full min-h-[56px] rounded-sm overflow-hidden border border-ink-border"
        role="img"
        aria-label="Case status distribution"
      >
        {STAGES.map((stage) => {
          const count = statusBreakdown[stage.key] || 0
          const pct = (count / total) * 100
          if (count === 0) return null
          return (
            <button
              key={stage.key}
              type="button"
              onClick={() => onFilter?.(stage.key)}
              className={`${stage.swatch} flex flex-col items-center justify-center text-ink min-w-[48px] transition-opacity hover:opacity-90`}
              style={{ width: `${pct}%` }}
              title={`${stage.label}: ${count}`}
              aria-label={`Filter ${stage.label}, ${count} cases`}
            >
              <span className={`font-mono text-sm font-semibold tabular ${stage.key === 'pending' || stage.key === 'do_not_retry' || stage.key === 'recovered' ? 'text-paper' : 'text-ink'}`}>
                {count}
              </span>
            </button>
          )
        })}
      </div>

      <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2">
        {STAGES.map((stage) => (
          <div key={stage.key} className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${stage.swatch}`} aria-hidden />
            <span className="font-sans text-xs text-paper/60">
              {stage.label}
              <span className="font-mono text-paper/40 ml-1 tabular">{statusBreakdown[stage.key] || 0}</span>
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}

export function HeroMetrics({ metrics }) {
  if (!metrics) {
    return <div className="h-36 rounded-sm border border-ink-border bg-ink-light animate-pulse mb-8" />
  }

  const breakdown = metrics.status_breakdown || {}
  const pending = breakdown.pending || 0
  const recovered = breakdown.recovered || 0
  const blocked = breakdown.do_not_retry || 0
  const review = breakdown.in_review || 0
  const processed = (metrics.total_cases || 0) - pending

  return (
    <section className="mb-8 grid grid-cols-1 md:grid-cols-12 gap-3" aria-label="Ledger summary">
      <div className="md:col-span-5 rounded-sm border border-verdigris/40 bg-ink-light p-5">
        <div className="font-sans text-[11px] uppercase tracking-[0.16em] text-verdigris-soft">
          Recovered revenue
        </div>
        <div className="font-display text-4xl md:text-5xl text-paper mt-1 tabular">
          {formatINR(metrics.recovered_revenue, { digits: 2 })}
        </div>
        <p className="font-sans text-xs text-paper/50 mt-2">
          Counted only after webhook confirms payment captured — not when an action is merely executed.
        </p>
      </div>

      <div className="md:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-3">
        <Stat label="Recoverable pool" value={formatINR(metrics.potentially_recoverable_revenue)} />
        <Stat label="Recovery rate" value={formatPct(metrics.recovery_rate)} />
        <Stat label="Action success" value={formatPct(metrics.action_success_rate)} />
        <Stat label="Cases processed" value={processed} />
        <Stat label="Recovered" value={recovered} />
        <Stat label="Blocked" value={blocked} />
        <Stat label="In review" value={review} />
        <Stat label="Pending" value={pending} />
        <Stat
          label="Agent accuracy"
          value={metrics.agent_accuracy != null ? formatPct(metrics.agent_accuracy) : '—'}
          hint={`n=${metrics.agent_accuracy_n}`}
        />
      </div>
    </section>
  )
}

function Stat({ label, value, hint }) {
  return (
    <div className="rounded-sm border border-ink-border bg-ink-light px-3 py-3">
      <div className="font-sans text-[10px] uppercase tracking-wide text-paper/45">{label}</div>
      <div className="font-mono text-lg text-paper tabular mt-0.5">{value}</div>
      {hint && <div className="font-sans text-[10px] text-paper/35">{hint}</div>}
    </div>
  )
}
