import { useEffect, useState, useCallback } from 'react'
import { api } from './api'
import Pipeline from './components/Pipeline'
import MetricsPanel from './components/MetricsPanel'
import CaseQueue from './components/CaseQueue'
import AuditTrail from './components/AuditTrail'

export default function App() {
  const [cases, setCases] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [auditEntries, setAuditEntries] = useState(null)
  const [busyCaseId, setBusyCaseId] = useState(null)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const [casesRes, metricsRes, auditRes] = await Promise.all([
        api.getCases(),
        api.getMetrics(),
        api.getAuditLog(),
      ])
      setCases(casesRes.cases)
      setMetrics(metricsRes)
      setAuditEntries(auditRes.entries)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 8000)
    return () => clearInterval(interval)
  }, [refresh])

  const handleProcess = async (caseId) => {
    setBusyCaseId(caseId)
    try {
      await api.processCase(caseId)
      await refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusyCaseId(null)
    }
  }

  const handleApprove = async (caseId) => {
    setBusyCaseId(caseId)
    try {
      await api.approveCase(caseId)
      await refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusyCaseId(null)
    }
  }

  return (
    <div className="min-h-screen bg-ink px-6 py-8 md:px-10 md:py-10">
      <header className="mb-8">
        <div className="font-sans text-xs uppercase tracking-widest text-brass mb-1">RecoverAI</div>
        <h1 className="font-display text-4xl md:text-5xl text-paper font-semibold">Recovery Ledger</h1>
        <p className="font-sans text-sm text-paper/50 mt-2">
          Live view of the payment recovery agent — every case, every decision, every guardrail.
        </p>
      </header>

      {error && (
        <div className="mb-6 bg-rust/20 border border-rust text-paper font-sans text-sm rounded-sm px-4 py-3">
          Couldn't reach the backend: {error}. Make sure <code className="font-mono">uvicorn app.main:app --reload</code> is running.
        </div>
      )}

      <Pipeline statusBreakdown={metrics?.status_breakdown} totalCases={metrics?.total_cases} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <h2 className="font-display text-2xl text-paper mb-3">Case Queue</h2>
          <CaseQueue
            cases={cases}
            onProcess={handleProcess}
            onApprove={handleApprove}
            busyCaseId={busyCaseId}
          />
        </div>

        <div className="space-y-8">
          <MetricsPanel metrics={metrics} />
          <AuditTrail entries={auditEntries} />
        </div>
      </div>

      <footer className="mt-10 font-sans text-xs text-paper/30">
        Refreshes automatically every 8s · Razorpay AI Buildathon 2026
      </footer>
    </div>
  )
}
