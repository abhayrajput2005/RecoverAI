function formatINR(amount) {
  if (amount == null) return '—'
  return `₹${amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

function StatCard({ label, value, accent = 'text-ink', sub }) {
  return (
    <div className="bg-paper rounded-sm p-4 border border-paper-dim">
      <div className="font-sans text-[11px] uppercase tracking-wide text-paper-text/60 mb-1">{label}</div>
      <div className={`font-mono text-2xl font-semibold tabular ${accent}`}>{value}</div>
      {sub && <div className="font-sans text-xs text-paper-text/50 mt-1">{sub}</div>}
    </div>
  )
}

export default function MetricsPanel({ metrics }) {
  if (!metrics) {
    return <div className="font-sans text-sm text-paper/50">Loading metrics…</div>
  }

  const fpAlert = metrics.false_positive_cost > 0

  return (
    <div>
      <h2 className="font-display text-2xl text-paper mb-3">Ledger Summary</h2>
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Recovered revenue" value={formatINR(metrics.recovered_revenue)} accent="text-verdigris" />
        <StatCard label="Recoverable pool" value={formatINR(metrics.potentially_recoverable_revenue)} />
        <StatCard
          label="Recovery rate"
          value={`${(metrics.recovery_rate * 100).toFixed(1)}%`}
        />
        <StatCard
          label="Action success rate"
          value={`${(metrics.action_success_rate * 100).toFixed(1)}%`}
        />
        <StatCard
          label="Agent accuracy"
          value={metrics.agent_accuracy != null ? `${(metrics.agent_accuracy * 100).toFixed(1)}%` : '—'}
          sub={`n=${metrics.agent_accuracy_n}`}
        />
        <StatCard
          label="False-positive cost"
          value={formatINR(metrics.false_positive_cost)}
          accent={fpAlert ? 'text-rust' : 'text-verdigris'}
          sub={fpAlert ? 'Guardrail breach — investigate' : 'Guardrail holding'}
        />
      </div>
    </div>
  )
}
