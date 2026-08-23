const STEPS = [
  { n: '1', title: 'Analysis', body: 'Failure code, gateway message, retry count, customer history.' },
  { n: '2', title: 'Recommendation', body: 'Deterministic classifier. Gemini only if the failure is ambiguous.' },
  { n: '3', title: 'Policy', body: 'authorize() — retry cap, terminal codes, high-value review. Models cannot skip this.' },
  { n: '4', title: 'Razorpay action', body: 'Test-mode retry or payment link only after policy allows it.' },
  { n: '5', title: 'Payment outcome', body: 'Recovered only after a verified webhook — not when an action is sent.' },
]

export default function GuardrailStrip() {
  return (
    <section
      className="mb-8 rounded-sm border border-ink-border bg-ink-light px-4 py-3"
      aria-label="Recovery decision flow"
    >
      <p className="font-sans text-[11px] uppercase tracking-[0.16em] text-brass mb-3">
        Analysis → Recommendation → Policy authorization → Razorpay action → Payment outcome
      </p>
      <ol className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
        {STEPS.map((step, i) => (
          <li key={step.n} className="relative rounded-sm border border-ink-border px-3 py-2">
            <div className="font-sans text-[10px] uppercase tracking-wide text-paper/40">
              {step.n} · {step.title}
            </div>
            <p className="font-sans text-xs text-paper/75 mt-1 leading-relaxed">{step.body}</p>
            {i < STEPS.length - 1 && (
              <span className="hidden lg:block absolute -right-2 top-4 text-brass/60 font-mono text-xs" aria-hidden>
                →
              </span>
            )}
          </li>
        ))}
      </ol>
    </section>
  )
}
