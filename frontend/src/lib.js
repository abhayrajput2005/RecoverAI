/** Display-only. The backend policy engine is the source of truth. */
export const RETRY_CAP = 3

export const STATUS = {
  pending: { label: 'Pending', tone: 'neutral' },
  ready: { label: 'Ready', tone: 'neutral' },
  in_review: { label: 'In Review', tone: 'warn' },
  action_taken: { label: 'Action Taken', tone: 'info' },
  recovered: { label: 'Recovered', tone: 'ok' },
  failed: { label: 'Failed', tone: 'bad' },
  do_not_retry: { label: 'Blocked', tone: 'bad' },
}

export const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'pending', label: 'Pending' },
  { key: 'in_review', label: 'In Review' },
  { key: 'action_taken', label: 'Action Taken' },
  { key: 'recovered', label: 'Recovered' },
  { key: 'failed', label: 'Failed' },
  { key: 'do_not_retry', label: 'Blocked' },
]

export const DEMO_PIN = ['RC-1001', 'RC-1099', 'RC-1055']

export function formatINR(amount, { digits = 0 } = {}) {
  if (amount == null || Number.isNaN(amount)) return '—'
  return `₹${Number(amount).toLocaleString('en-IN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`
}

export function formatPct(value) {
  if (value == null) return '—'
  return `${(value * 100).toFixed(1)}%`
}

export function statusLabel(status) {
  return STATUS[status]?.label || status || 'Unknown'
}

export function formatAction(action) {
  if (!action) return '—'
  return action.replace(/_/g, ' ')
}

export function formatWhen(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-IN', { hour12: false })
}

export function classifySource(bucket) {
  if (bucket === 'ambiguous') return 'Gemini assists recommendation'
  if (bucket === 'adversarial') return 'Deterministic classifier (terminal)'
  if (bucket === 'clear' || bucket === 'edge') return 'Deterministic classifier'
  return 'Not classified yet'
}

export function messageForResult(result, verb = 'process') {
  if (!result) return { title: 'Done', body: 'Request completed.', tone: 'info' }

  if (result.blocked_reason) {
    return {
      title: 'Policy blocked execution',
      body: result.blocked_reason,
      tone: 'warn',
    }
  }

  if (result.action === 'do_not_retry') {
    return {
      title: 'Blocked — no payment action',
      body: `${result.case_id} was classified as not retryable. Policy did not call Razorpay.`,
      tone: 'bad',
    }
  }

  if (result.action === 'escalate_human_review' || result.executed === false && result.note) {
    return {
      title: 'Held for human review',
      body: `${result.case_id} exceeds the high-value auto-action threshold. Approve to authorize Razorpay execution.`,
      tone: 'warn',
    }
  }

  if (result.executed === true) {
    return {
      title: 'Recovery action executed',
      body: `${formatAction(result.action)} sent in Razorpay test mode for ${result.case_id}. Awaiting payment outcome — this is not recovered yet.`,
      tone: 'ok',
    }
  }

  return {
    title: verb === 'approve' ? 'Approval recorded' : 'Decision recorded',
    body: `Action: ${formatAction(result.action)}. Executed: ${String(result.executed)}.`,
    tone: 'info',
  }
}

export function sortCases(cases) {
  const pin = new Map(DEMO_PIN.map((id, i) => [id, i]))
  return [...cases].sort((a, b) => {
    const pa = pin.has(a.case_id) ? pin.get(a.case_id) : 99
    const pb = pin.has(b.case_id) ? pin.get(b.case_id) : 99
    if (pa !== pb) return pa - pb
    const rank = {
      in_review: 0,
      pending: 1,
      action_taken: 2,
      recovered: 3,
      failed: 4,
      do_not_retry: 5,
    }
    const ra = rank[a.status] ?? 9
    const rb = rank[b.status] ?? 9
    if (ra !== rb) return ra - rb
    return (b.amount || 0) - (a.amount || 0)
  })
}

export function latestDecision(entries, caseId) {
  if (!entries) return null
  const relevant = entries.filter(
    (e) =>
      e.case_id === caseId &&
      ['deterministic', 'llm', 'policy_override'].includes(e.source) &&
      e.payload?.recommended_action,
  )
  return relevant.length ? relevant[relevant.length - 1] : null
}

export function latestPolicy(entries, caseId) {
  if (!entries) return null
  const relevant = entries.filter((e) => e.case_id === caseId && e.source === 'policy_override')
  return relevant.length ? relevant[relevant.length - 1] : null
}

export function latestWebhook(entries, caseId) {
  if (!entries) return null
  const relevant = entries.filter((e) => e.case_id === caseId && e.source === 'webhook')
  return relevant.length ? relevant[relevant.length - 1] : null
}

export function policyVerdict(c, policyEntry) {
  const rec = policyEntry?.payload?.recommended_action
  if (c.status === 'do_not_retry') return rec ? `BLOCKED · ${formatAction(rec)}` : 'BLOCKED · no Razorpay execution'
  if (c.status === 'in_review') return 'HELD · awaiting human approval'
  if (c.status === 'action_taken') return rec ? `AUTHORIZED · ${formatAction(rec)}` : 'AUTHORIZED · Razorpay action sent'
  if (c.status === 'recovered') return rec ? `AUTHORIZED · ${formatAction(rec)}` : 'AUTHORIZED · payment captured'
  if (c.status === 'failed') return 'AUTHORIZED · payment failed after action'
  if (rec) return `Pending authorization · ${formatAction(rec)}`
  return 'Not yet authorized'
}

export function outcomeLabel(c) {
  if (c.status === 'recovered') return 'Recovered'
  if (c.status === 'failed') return 'Failed'
  if (c.status === 'do_not_retry') return 'Blocked — not recovered'
  if (c.status === 'action_taken') return 'Awaiting payment outcome'
  if (c.status === 'in_review') return 'Human review'
  return 'No outcome yet'
}

export function storySteps(c) {
  const classified = Boolean(c.classification_bucket)
  const decided = classified || ['in_review', 'action_taken', 'recovered', 'failed', 'do_not_retry'].includes(c.status)
  const authorized = ['in_review', 'action_taken', 'recovered', 'failed', 'do_not_retry'].includes(c.status)
  const executed = Boolean(c.razorpay_reference_id) || c.status === 'action_taken' || c.status === 'recovered' || c.status === 'failed'
  const blocked = c.status === 'do_not_retry'
  const outcome = c.status === 'recovered' || c.status === 'failed' || blocked

  return [
    { key: 'analysis', label: 'Analysis', done: classified || decided, note: c.failure_code || '—' },
    { key: 'recommendation', label: 'Recommendation', done: decided, note: formatAction(c.last_action) !== '—' ? formatAction(c.last_action) : c.classification_bucket || '—' },
    { key: 'policy', label: 'Policy', done: authorized, note: blocked ? 'BLOCKED' : authorized ? (c.status === 'in_review' ? 'HELD' : 'AUTHORIZED') : '—' },
    { key: 'razorpay', label: 'Razorpay', done: executed && !blocked, note: blocked ? 'No execution' : c.razorpay_reference_id || (c.status === 'action_taken' ? 'TEST action sent' : '—') },
    { key: 'outcome', label: 'Outcome', done: outcome, note: outcomeLabel(c) },
  ]
}
