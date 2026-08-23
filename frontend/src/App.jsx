import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api'
import { messageForResult } from './lib'
import Pipeline, { HeroMetrics } from './components/Pipeline'
import MetricsPanel from './components/MetricsPanel'
import CaseQueue from './components/CaseQueue'
import AuditTrail from './components/AuditTrail'
import GuardrailStrip from './components/GuardrailStrip'
import CaseDetail from './components/CaseDetail'

export default function App() {
  const [cases, setCases] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [auditEntries, setAuditEntries] = useState(null)
  const [busyCaseId, setBusyCaseId] = useState(null)
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)
  const [online, setOnline] = useState(true)
  const [filter, setFilter] = useState('all')
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const refresh = useCallback(async ({ silent } = {}) => {
    if (!silent) setRefreshing(true)
    try {
      const [health, casesRes, metricsRes, auditRes] = await Promise.all([
        api.getHealth(),
        api.getCases(),
        api.getMetrics(),
        api.getAuditLog(),
      ])
      if (health?.status !== 'ok') {
        throw new Error('Backend health check did not return ok.')
      }
      setCases(casesRes.cases)
      setMetrics(metricsRes)
      setAuditEntries(auditRes.entries)
      setError(null)
      setOnline(true)
    } catch (e) {
      setError(e.message)
      setOnline(false)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(() => {
      if (document.hidden) return
      refresh({ silent: true })
    }, 12000)
    return () => clearInterval(interval)
  }, [refresh])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') setSelectedId(null)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const selected = useMemo(
    () => (cases || []).find((c) => c.case_id === selectedId) || null,
    [cases, selectedId],
  )

  const runAction = async (caseId, fn, verb) => {
    if (busyCaseId) return
    setBusyCaseId(caseId)
    setNotice(null)
    try {
      const result = await fn(caseId)
      setNotice(messageForResult(result, verb))
      await refresh()
    } catch (e) {
      setError(e.message)
      const title =
        e.status === 404
          ? 'Case not found'
          : e.status === 500
            ? 'Backend error'
            : e.message?.includes('timed out')
              ? 'Request timed out'
              : 'Request failed'
      setNotice({
        title,
        body: e.message,
        tone: 'bad',
      })
    } finally {
      setBusyCaseId(null)
    }
  }

  const handleProcess = (caseId) => runAction(caseId, api.processCase, 'process')
  const handleApprove = (caseId) => runAction(caseId, api.approveCase, 'approve')

  const noticeClass = {
    ok: 'border-verdigris/50 bg-verdigris/10',
    warn: 'border-brass/50 bg-brass/10',
    bad: 'border-rust/50 bg-rust/10',
    info: 'border-ink-border bg-ink-light',
  }

  return (
    <div className="min-h-screen bg-ink px-4 py-6 md:px-8 md:py-8">
      <header className="mb-6 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <div className="font-sans text-xs uppercase tracking-[0.22em] text-brass mb-1">RecoverAI</div>
          <h1 className="font-display text-4xl md:text-5xl text-paper font-semibold">Recovery Ledger</h1>
          <p className="font-sans text-sm text-paper/50 mt-2 max-w-xl">
            Merchant operations console for failed-payment recovery. Recommendations never execute until policy authorizes them.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`font-sans text-xs px-2 py-1 rounded-sm border ${
              online ? 'border-verdigris/40 text-verdigris-soft' : 'border-rust/40 text-rust-soft'
            }`}
          >
            {online ? 'API live' : 'API offline'}
          </span>
          <button
            type="button"
            onClick={() => refresh()}
            disabled={refreshing || Boolean(busyCaseId)}
            className="px-3 py-1.5 rounded-sm border border-ink-border text-paper font-sans text-xs hover:bg-ink-light disabled:opacity-40"
          >
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-4 border border-rust text-paper font-sans text-sm rounded-sm px-4 py-3" role="alert">
          Couldn&apos;t reach the backend: {error}. Run{' '}
          <code className="font-mono">uvicorn app.main:app --reload --host 127.0.0.1 --port 8000</code> from{' '}
          <code className="font-mono">backend/</code>.
        </div>
      )}

      {notice && (
        <div className={`mb-4 border rounded-sm px-4 py-3 font-sans text-sm text-paper ${noticeClass[notice.tone] || noticeClass.info}`} role="status">
          <div className="font-medium">{notice.title}</div>
          <div className="text-paper/70 mt-0.5">{notice.body}</div>
        </div>
      )}

      <GuardrailStrip />
      <HeroMetrics metrics={metrics} />
      <Pipeline
        statusBreakdown={metrics?.status_breakdown}
        totalCases={metrics?.total_cases}
        onFilter={setFilter}
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        <div className="xl:col-span-7">
          <h2 className="font-display text-2xl text-paper mb-3">Case queue</h2>
          {loading && !cases ? (
            <div className="font-sans text-sm text-paper/50">Loading cases…</div>
          ) : (
            <CaseQueue
              cases={cases}
              filter={filter}
              query={query}
              onFilter={setFilter}
              onQuery={setQuery}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onProcess={handleProcess}
              onApprove={handleApprove}
              busyCaseId={busyCaseId}
            />
          )}
        </div>

        <div className="xl:col-span-5 space-y-8">
          {selected ? (
            <CaseDetail
              caseRecord={selected}
              auditEntries={auditEntries}
              onClose={() => setSelectedId(null)}
              onProcess={handleProcess}
              onApprove={handleApprove}
              busy={busyCaseId === selected.case_id}
            />
          ) : (
            <div className="rounded-sm border border-dashed border-ink-border p-6 font-sans text-sm text-paper/45">
              Select a case to inspect transaction, policy decision, Razorpay reference, and audit trail.
            </div>
          )}
          <MetricsPanel metrics={metrics} />
          <AuditTrail entries={auditEntries} highlightCaseId={selectedId} onSelectCase={setSelectedId} />
        </div>
      </div>

      <footer className="mt-10 font-sans text-xs text-paper/30">
        Auto-refresh 12s while this tab is visible · Razorpay AI Buildathon 2026
      </footer>
    </div>
  )
}
