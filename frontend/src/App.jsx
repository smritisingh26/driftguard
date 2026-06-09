import { useState, useEffect } from 'react'
import { getRuns, clearRuns } from './utils/api'
import RunForm from './components/RunForm'
import RunPanel from './components/RunPanel'
import CompareView from './components/CompareView'
import Header from './components/Header'

export default function App() {
  const [runs, setRuns] = useState([])
  const [activeRun, setActiveRun] = useState(null)
  const [compareMode, setCompareMode] = useState(false)
  const [compareRuns, setCompareRuns] = useState([null, null])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    getRuns()
      .then(runs => runs.sort((a, b) => b.created_at - a.created_at))
      .then(setRuns)
      .catch(() => {})
  }, [])

  function onRunComplete(run) {
    setRuns(prev => [run, ...prev])
    setActiveRun(run)
    setError(null)
  }

  function onError(msg) {
    setError(msg)
    setLoading(false)
  }

  async function onClear() {
    await clearRuns()
    setRuns([])
    setActiveRun(null)
    setCompareRuns([null, null])
  }

  function toggleCompare(run) {
    setCompareRuns(prev => {
      if (prev[0]?.run_id === run.run_id) return [null, prev[1]]
      if (prev[1]?.run_id === run.run_id) return [prev[0], null]
      if (!prev[0]) return [run, prev[1]]
      if (!prev[1]) return [prev[0], run]
      return [run, prev[1]]
    })
  }

  return (
    <div className="min-h-screen bg-drift-bg text-drift-text">
      <Header
        runsCount={runs.length}
        compareMode={compareMode}
        setCompareMode={setCompareMode}
        onClear={onClear}
      />

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Run Form */}
        <RunForm
          onRunComplete={onRunComplete}
          onError={onError}
          loading={loading}
          setLoading={setLoading}
        />

        {error && (
          <div className="bg-red-900/20 border border-drift-danger/40 rounded-xl p-4 text-drift-danger text-sm fade-in">
            {error}
          </div>
        )}

        {/* Compare Mode */}
        {compareMode && (
          <CompareView
            runs={runs}
            compareRuns={compareRuns}
            toggleCompare={toggleCompare}
          />
        )}

        {/* Active Run */}
        {!compareMode && activeRun && (
          <RunPanel run={activeRun} />
        )}

        {/* Run History */}
        {runs.length > 0 && (
          <div className="fade-in">
            <h2 className="font-display text-sm font-semibold text-drift-subtle uppercase tracking-widest mb-4">
              Run History
            </h2>
            <div className="grid gap-3">
              {runs.map(run => (
                <button
                  key={run.run_id}
                  onClick={() => { setActiveRun(run); setCompareMode(false) }}
                  className={`w-full text-left px-5 py-4 rounded-xl border transition-all duration-200
                    ${activeRun?.run_id === run.run_id
                      ? 'bg-drift-surface border-drift-accent/50'
                      : 'bg-drift-surface border-drift-border hover:border-drift-muted'
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{run.run_label}</span>
                        <span className="text-drift-subtle text-xs font-mono">
                          {new Date(run.created_at * 1000).toLocaleString([], {
                            month: 'short', day: 'numeric',
                            hour: '2-digit', minute: '2-digit'
                          })}
                        </span>
                      </div>
                      <p className="text-drift-subtle text-xs mt-1 font-mono truncate max-w-md">
                        {run.inferred_intent}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 ml-4 shrink-0">
                      {run.summary.unrecovered_drift ? (
                        <span className="text-xs px-2 py-1 rounded-full bg-drift-danger/15 text-drift-danger border border-drift-danger/30">
                          Drift
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-1 rounded-full bg-drift-ok/15 text-drift-ok border border-drift-ok/30">
                          On track
                        </span>
                      )}
                      <span className="text-drift-subtle text-xs font-mono">
                        {run.summary.total_steps} steps
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
