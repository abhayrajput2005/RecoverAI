const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const { timeout = 20000, ...fetchOptions } = options
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      ...fetchOptions,
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const detail =
        typeof body.detail === 'string'
          ? body.detail
          : body.detail
            ? JSON.stringify(body.detail)
            : `Request failed (${res.status})`
      const err = new Error(detail)
      err.status = res.status
      throw err
    }
    return res.json()
  } catch (e) {
    if (e.name === 'AbortError') {
      throw new Error('Request timed out. Check that the backend is running.')
    }
    if (e.message === 'Failed to fetch' || e.message === 'NetworkError when attempting to fetch resource.') {
      throw new Error('Backend unreachable. Start uvicorn on port 8000.')
    }
    throw e
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  getHealth: () => request('/health', { timeout: 8000 }),
  getCases: () => request('/cases'),
  getCase: (caseId) => request(`/cases/${caseId}`),
  getMetrics: () => request('/metrics'),
  getAuditLog: () => request('/audit-log'),
  processCase: (caseId) =>
    request(`/cases/${caseId}/process`, { method: 'POST', timeout: 60000 }),
  approveCase: (caseId) =>
    request(`/cases/${caseId}/approve`, { method: 'POST', timeout: 60000 }),
}

export { BASE_URL }
