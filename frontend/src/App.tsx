import { useEffect, useState } from 'react'

type Health = { status: string }

const NAV = ['Overview', 'Berth Gantt', 'Queue', 'Shift Plan', 'Compare', 'Live Map']

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(setHealth)
      .catch((e) => setError(String(e)))
  }, [])

  const apiBadge = health
    ? health.status === 'ok'
      ? '🟢 API online'
      : `⚠️ ${health.status}`
    : error
      ? '🔴 API offline'
      : '⏳ connecting…'

  return (
    <div className="min-h-screen bg-port-bg text-slate-200">
      <header className="flex items-center gap-4 border-b border-port-line bg-port-panel/60 px-6 py-4">
        <span className="text-2xl">🚢</span>
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Port Congestion Optimiser</h1>
          <p className="text-xs text-slate-400">
            Container Congestion Predictor &amp; Port Operations Optimiser
          </p>
        </div>
        <span className="ml-auto rounded-full border border-port-line bg-port-panel px-3 py-1 text-xs">
          {apiBadge}
        </span>
      </header>

      <nav className="flex gap-1 border-b border-port-line px-6 py-3 text-sm">
        {NAV.map((item) => (
          <span
            key={item}
            className="cursor-not-allowed rounded-md px-3 py-1.5 text-slate-400 hover:bg-port-panel/60"
          >
            {item}
          </span>
        ))}
      </nav>

      <main className="mx-auto max-w-4xl px-6 py-10">
        <div className="rounded-xl border border-port-line bg-port-panel p-6">
          <h2 className="mb-2 font-semibold">Phase 1 — scaffold complete</h2>
          <p className="text-sm text-slate-400">
            Frontend shell + backend API wired through the Vite dev proxy. The six screens
            arrive in P9–P12; the core engine (synthetic data → simulation → prediction →
            CP-SAT optimisation → 72 h shift plan) lands in P2–P8.
          </p>
        </div>
      </main>
    </div>
  )
}
