import { formatINR } from '../lib'

export default function MetricsPanel({ metrics }) {
  if (!metrics) {
    return <div className="font-sans text-sm text-paper/50">Loading metrics…</div>
  }

  const fp = metrics.false_positive_cost > 0
  const fpPending = (metrics.false_positive_case_ids || []).length

  return (
    <div>
      <h2 className="font-display text-xl text-paper mb-3">Risk & accuracy</h2>
      <div className="space-y-3">
        <div className="rounded-sm border border-ink-border bg-ink-light p-4">
          <div className="font-sans text-[11px] uppercase tracking-wide text-paper/45">
            False-positive cost
          </div>
          <div className={`font-mono text-2xl tabular mt-1 ${fp ? 'text-brass' : 'text-verdigris-soft'}`}>
            {formatINR(metrics.false_positive_cost)}
          </div>
          <p className="font-sans text-xs text-paper/50 mt-2 leading-relaxed">
            {fp
              ? `${fpPending} adversarial case${fpPending === 1 ? '' : 's'} are not yet in Blocked status (includes unprocessed). Process them through policy — this is not the same as a Razorpay execution.`
              : 'Every adversarial case is Blocked. Guardrail holding.'}
          </p>
        </div>
      </div>
    </div>
  )
}
