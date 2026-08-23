const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  getCases: () => request('/cases'),
  getMetrics: () => request('/metrics'),
  getAuditLog: () => request('/audit-log'),
  processCase: (caseId) => request(`/cases/${caseId}/process`, { method: 'POST' }),
  approveCase: (caseId) => request(`/cases/${caseId}/approve`, { method: 'POST' }),
}
