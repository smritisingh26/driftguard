import { BarChart2, GitCompare, Trash2 } from 'lucide-react'

export default function Header({ runsCount, compareMode, setCompareMode, onClear }) {
  return (
    <header className="border-b border-drift-border bg-drift-surface/60 backdrop-blur sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart2 className="text-drift-accent" size={22} />
          <span className="font-display text-xl font-bold tracking-tight">DriftGuard</span>
          <span className="text-xs text-drift-subtle font-mono ml-2">
            Agent Trajectory Observability
          </span>
        </div>
        <div className="flex items-center gap-3">
          {runsCount > 1 && (
            <button
              onClick={() => setCompareMode(v => !v)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all
                ${compareMode
                  ? 'bg-drift-accent/20 text-drift-accent border border-drift-accent/40'
                  : 'border border-drift-border text-drift-subtle hover:text-drift-text hover:border-drift-muted'
                }`}
            >
              <GitCompare size={15} />
              Compare Runs
            </button>
          )}
          {runsCount > 0 && (
            <button
              onClick={onClear}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm border border-drift-border text-drift-subtle hover:text-drift-danger hover:border-drift-danger/40 transition-all"
            >
              <Trash2 size={15} />
              Clear
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
