import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Legend
} from 'recharts'

const THRESHOLD = 0.35

function MiniChart({ run, color }) {
  if (!run) return (
    <div className="h-40 flex items-center justify-center text-drift-muted text-sm border border-dashed border-drift-border rounded-xl">
      Select a run to compare
    </div>
  )
  const data = run.steps.map(s => ({
    name: `S${s.step_index + 1}`,
    'Per-step': s.per_step_score,
    'Trajectory': s.trajectory_score,
  }))
  return (
    <ResponsiveContainer width="100%" height={160}>
      <ComposedChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#8B8FA8' }} axisLine={false} tickLine={false} />
        <YAxis domain={[0, 0.8]} tick={{ fontSize: 10, fill: '#8B8FA8' }} axisLine={false} tickLine={false} />
        <ReferenceLine y={THRESHOLD} stroke="#FF5C5C" strokeDasharray="4 4" strokeWidth={1} />
        <Bar dataKey="Per-step" fill={color} opacity={0.6} radius={[2, 2, 0, 0]} />
        <Line type="monotone" dataKey="Trajectory" stroke="#52D68A" strokeWidth={1.5} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

function RunSelector({ runs, selected, onToggle, color }) {
  return (
    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
      {runs.map(run => (
        <button
          key={run.run_id}
          onClick={() => onToggle(run)}
          className={`w-full text-left px-4 py-3 rounded-xl border text-sm transition-all
            ${selected?.run_id === run.run_id
              ? `border-[${color}]/50 bg-[${color}]/10`
              : 'border-drift-border hover:border-drift-muted bg-drift-bg'
            }`}
          style={selected?.run_id === run.run_id ? { borderColor: color, backgroundColor: color + '18' } : {}}
        >
          <div className="font-medium truncate">{run.run_label}</div>
          <div className="text-xs text-drift-subtle font-mono mt-0.5 truncate">{run.inferred_intent}</div>
        </button>
      ))}
    </div>
  )
}

function CompareCard({ run, color, label }) {
  if (!run) return (
    <div className="bg-drift-surface border border-dashed border-drift-border rounded-2xl p-6 flex items-center justify-center text-drift-muted text-sm">
      No run selected
    </div>
  )
  return (
    <div className="bg-drift-surface border border-drift-border rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-widest" style={{ color }}>{label}</span>
        <span className={`text-xs px-2 py-1 rounded-full ${run.summary.unrecovered_drift ? 'bg-drift-danger/15 text-drift-danger' : 'bg-drift-ok/15 text-drift-ok'}`}>
          {run.summary.unrecovered_drift ? 'Drifted' : 'On track'}
        </span>
      </div>
      <div className="font-medium text-sm">{run.run_label}</div>
      <p className="text-xs font-mono text-drift-subtle">{run.inferred_intent}</p>
      <MiniChart run={run} color={color} />
      <div className="grid grid-cols-3 gap-3 pt-2 border-t border-drift-border">
        {[
          { label: 'Steps', value: run.summary.total_steps },
          { label: 'Drift steps', value: run.summary.drift_steps },
          { label: 'Traj. score', value: run.summary.mean_trajectory_score?.toFixed(3) },
        ].map(({ label, value }) => (
          <div key={label} className="text-center">
            <div className="text-xs text-drift-subtle mb-0.5">{label}</div>
            <div className="font-mono font-semibold text-sm">{value}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function CompareView({ runs, compareRuns, toggleCompare }) {
  const [a, b] = compareRuns

  return (
    <div className="space-y-6 fade-in">
      <div className="bg-drift-surface border border-drift-border rounded-2xl p-6">
        <h2 className="font-display font-semibold text-sm uppercase tracking-widest text-drift-subtle mb-4">
          Select runs to compare
        </h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <div className="text-xs font-semibold text-[#6C8EFF] uppercase tracking-widest mb-3">Run A</div>
            <RunSelector runs={runs} selected={a} onToggle={toggleCompare} color="#6C8EFF" />
          </div>
          <div>
            <div className="text-xs font-semibold text-[#FFB347] uppercase tracking-widest mb-3">Run B</div>
            <RunSelector runs={runs} selected={b} onToggle={toggleCompare} color="#FFB347" />
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <CompareCard run={a} color="#6C8EFF" label="Run A" />
        <CompareCard run={b} color="#FFB347" label="Run B" />
      </div>
    </div>
  )
}
