import { useState } from 'react'
import { Play, ChevronDown, ChevronUp, FileText, Code2 } from 'lucide-react'
import { postRun } from '../utils/api'

const DEMOS = {
  lease_qa: {
    userMessage: "Please review this lease agreement and identify any clauses that could be risky or problematic for a tenant.",
    distractionMessage: "Actually, can you also check what the monthly rent and payment schedule is?",
    runLabel: "Lease Risk Analysis",
  },
  code_gen: {
    userMessage: "Write a Python function that validates email addresses using regex. It should return True if valid, False otherwise, and handle edge cases like None, empty string, and malformed addresses.",
    distractionMessage: "Forget the email validator. I need you to build a scikit-learn machine learning pipeline that trains a customer churn prediction model on tabular CRM data, with feature scaling and cross-validation.",
    runLabel: "Code Gen: Goal Drift",
  },
}

export default function RunForm({ onRunComplete, onError, loading, setLoading }) {
  const [userMessage, setUserMessage] = useState('')
  const [distractionMessage, setDistractionMessage] = useState('')
  const [runLabel, setRunLabel] = useState('')
  const [scenario, setScenario] = useState('lease_qa')
  const [showAdvanced, setShowAdvanced] = useState(false)

  async function handleSubmit() {
    if (!userMessage.trim()) return
    setLoading(true)
    try {
      const run = await postRun({ userMessage, distractionMessage, runLabel, scenario })
      onRunComplete(run)
    } catch (e) {
      onError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function loadDemo(type) {
    const d = DEMOS[type]
    setUserMessage(d.userMessage)
    setDistractionMessage(d.distractionMessage)
    setRunLabel(d.runLabel)
    setScenario(type)
    setShowAdvanced(true)
  }

  return (
    <div className="bg-drift-surface border border-drift-border rounded-2xl p-6 fade-in">
      <div className="flex items-start justify-between mb-5 gap-3">
        <h2 className="font-display text-lg font-semibold shrink-0">New Run</h2>
        <div className="flex flex-wrap gap-2 justify-end">
          <button
            onClick={() => loadDemo('lease_qa')}
            className="flex items-center gap-1.5 text-xs text-drift-accent hover:text-drift-accent/80 border border-drift-accent/30 hover:border-drift-accent/60 px-3 py-1.5 rounded-lg transition-all"
          >
            <FileText size={12} />
            Load Document QA Demo
          </button>
          <button
            onClick={() => loadDemo('code_gen')}
            className="flex items-center gap-1.5 text-xs text-drift-accent hover:text-drift-accent/80 border border-drift-accent/30 hover:border-drift-accent/60 px-3 py-1.5 rounded-lg transition-all"
          >
            <Code2 size={12} />
            Load Code Gen Demo
          </button>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-xs text-drift-subtle uppercase tracking-widest mb-2 font-semibold">
            User Message
          </label>
          <textarea
            value={userMessage}
            onChange={e => setUserMessage(e.target.value)}
            rows={3}
            placeholder="What should the agent do?"
            className="w-full bg-drift-bg border border-drift-border rounded-xl px-4 py-3 text-sm text-drift-text placeholder-drift-muted resize-none focus:outline-none focus:border-drift-accent/60 transition-colors font-mono"
          />
        </div>

        <button
          onClick={() => setShowAdvanced(v => !v)}
          className="flex items-center gap-2 text-xs text-drift-subtle hover:text-drift-text transition-colors"
        >
          {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          Advanced options
        </button>

        {showAdvanced && (
          <div className="space-y-4 pt-2 fade-in">
            <div>
              <label className="block text-xs text-drift-subtle uppercase tracking-widest mb-2 font-semibold">
                Distraction Message
                <span className="ml-2 normal-case text-drift-muted font-normal">
                  (injected mid-run to trigger drift)
                </span>
              </label>
              <textarea
                value={distractionMessage}
                onChange={e => setDistractionMessage(e.target.value)}
                rows={2}
                placeholder="Optional: a follow-up message that pivots the agent's focus..."
                className="w-full bg-drift-bg border border-drift-border rounded-xl px-4 py-3 text-sm text-drift-text placeholder-drift-muted resize-none focus:outline-none focus:border-drift-accent/60 transition-colors font-mono"
              />
            </div>

            <div>
              <label className="block text-xs text-drift-subtle uppercase tracking-widest mb-2 font-semibold">
                Run Label
              </label>
              <input
                value={runLabel}
                onChange={e => setRunLabel(e.target.value)}
                placeholder="e.g. Lease Risk Analysis"
                className="w-full bg-drift-bg border border-drift-border rounded-xl px-4 py-3 text-sm text-drift-text placeholder-drift-muted focus:outline-none focus:border-drift-accent/60 transition-colors"
              />
            </div>
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={loading || !userMessage.trim()}
          className="flex items-center gap-2 px-6 py-3 bg-drift-accent hover:bg-drift-accent/90 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl font-medium text-sm transition-all"
        >
          {loading ? (
            <>
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Running agent...
            </>
          ) : (
            <>
              <Play size={15} />
              Run Agent
            </>
          )}
        </button>
      </div>
    </div>
  )
}
