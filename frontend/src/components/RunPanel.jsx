import { useState } from 'react'
import {
  Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Legend, ComposedChart, Cell
} from 'recharts'
import { AlertTriangle, CheckCircle, TrendingDown, Zap, ChevronDown, ChevronUp } from 'lucide-react'

function ScoreBadge({ score, threshold }) {
  const over = score > threshold
  return (
    <span className={`inline-block text-xs font-mono px-2 py-0.5 rounded-full
      ${over ? 'bg-drift-danger/15 text-drift-danger' : 'bg-drift-ok/15 text-drift-ok'}`}>
      {score.toFixed(3)}
    </span>
  )
}

function StatCard({ label, value, sub, color }) {
  return (
    <div className="bg-drift-bg border border-drift-border rounded-xl p-4">
      <div className="text-xs text-drift-subtle uppercase tracking-widest mb-1 font-semibold">{label}</div>
      <div className={`text-2xl font-display font-bold ${color || 'text-drift-text'}`}>{value}</div>
      {sub && <div className="text-xs text-drift-muted mt-1">{sub}</div>}
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-drift-surface border border-drift-border rounded-xl p-3 text-xs space-y-1 shadow-xl">
      <div className="font-semibold text-drift-text mb-2">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2">
          <span style={{ color: p.color }}>{p.name}:</span>
          <span className="font-mono text-drift-text">{p.value?.toFixed(4)}</span>
        </div>
      ))}
    </div>
  )
}

export default function RunPanel({ run }) {
  const [expandedStep, setExpandedStep] = useState(null)
  const threshold = run.drift_threshold ?? 0.55

  const chartData = run.steps.map((s, i) => ({
    name: `Step ${s.step_index + 1}`,
    tool: s.tool_name,
    'Per-step drift': s.per_step_score,
    'Trajectory score': s.trajectory_score,
    isDrift: s.is_drift,
    isRecovery: s.is_recovery,
  }))

  const { summary } = run
  const tokenCost = ((summary.total_tokens || 0) * 0.0000002).toFixed(6)

  return (
    <div className="space-y-6 fade-in">

      {/* Intent banner */}
      <div className="bg-drift-surface border border-drift-border rounded-2xl p-5">
        <div className="text-xs text-drift-subtle uppercase tracking-widest mb-2 font-semibold">
          Inferred Intent
        </div>
        <p className="text-drift-text font-mono text-sm leading-relaxed">
          {run.inferred_intent}
        </p>
        {run.distraction_message && (
          <div className="mt-3 pt-3 border-t border-drift-border">
            <div className="text-xs text-drift-warn uppercase tracking-widest mb-1 font-semibold">
              Distraction injected
            </div>
            <p className="text-drift-subtle font-mono text-sm">{run.distraction_message}</p>
          </div>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Status"
          value={summary.unrecovered_drift ? 'Drifted' : 'On Track'}
          color={summary.unrecovered_drift ? 'text-drift-danger' : 'text-drift-ok'}
          sub={summary.unrecovered_drift ? 'Unrecovered drift detected' : 'Intent maintained'}
        />
        <StatCard
          label="Drift Steps"
          value={`${summary.drift_steps} / ${summary.total_steps}`}
          color={summary.drift_steps > 0 ? 'text-drift-warn' : 'text-drift-ok'}
          sub="steps above threshold"
        />
        <StatCard
          label="Trajectory Score"
          value={summary.mean_trajectory_score?.toFixed(3)}
          color={summary.mean_trajectory_score > threshold ? 'text-drift-danger' : 'text-drift-ok'}
          sub="mean coherence score"
        />
        <StatCard
          label="Token Cost"
          value={`$${tokenCost}`}
          sub={`${summary.total_tokens} total tokens`}
        />
      </div>

      {/* Drift chart */}
      <div className="bg-drift-surface border border-drift-border rounded-2xl p-6">
        <h3 className="font-display font-semibold text-sm uppercase tracking-widest text-drift-subtle mb-5">
          Drift Timeline
        </h3>
        <ResponsiveContainer width="100%" height={240}>
          <ComposedChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#8B8FA8' }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 0.8]} tick={{ fontSize: 11, fill: '#8B8FA8' }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '11px', color: '#8B8FA8', paddingTop: '16px' }}
            />
            <ReferenceLine
              y={threshold}
              stroke="#FF5C5C"
              strokeDasharray="5 5"
              strokeWidth={1.5}
              label={{ value: 'threshold', position: 'insideTopRight', fontSize: 10, fill: '#FF5C5C' }}
            />
            <Bar dataKey="Per-step drift" radius={[3, 3, 0, 0]} label={false}>
              {chartData.map((entry, index) => (
                <Cell
                  key={index}
                  fill={entry.isDrift ? '#FF5C5C' : '#6C8EFF'}
                  opacity={0.8}
                />
              ))}
            </Bar>
            <Line
              type="monotone"
              dataKey="Trajectory score"
              stroke="#52D68A"
              strokeWidth={2}
              dot={{ fill: '#52D68A', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Step-by-step breakdown */}
      <div className="bg-drift-surface border border-drift-border rounded-2xl p-6">
        <h3 className="font-display font-semibold text-sm uppercase tracking-widest text-drift-subtle mb-5">
          Step Breakdown
        </h3>
        <div className="space-y-3">
          {run.steps.map((step, i) => (
            <div key={i}>
              {step.from_distraction && (i === 0 || !run.steps[i - 1].from_distraction) && (
                <div className="flex items-center gap-3 my-4">
                  <div className="flex-1 h-px bg-drift-warn/40" />
                  <span className="text-xs font-semibold text-drift-warn uppercase tracking-widest px-2">
                    Distraction injected
                  </span>
                  <div className="flex-1 h-px bg-drift-warn/40" />
                </div>
              )}
              <div
                className={`border rounded-xl overflow-hidden transition-all
                  ${step.is_drift
                    ? 'border-drift-danger/40 bg-drift-danger/5'
                    : step.is_recovery
                    ? 'border-drift-ok/40 bg-drift-ok/5'
                    : 'border-drift-border bg-drift-bg'
                  }`}
              >
                <button
                  onClick={() => setExpandedStep(expandedStep === i ? null : i)}
                  className="w-full flex items-center justify-between px-4 py-3 text-left"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-drift-muted flex items-center justify-center text-xs font-mono font-bold text-drift-subtle shrink-0">
                      {step.step_index + 1}
                    </span>
                    <div>
                      <span className="text-sm font-medium">{step.tool_name}</span>
                      {step.is_drift && (
                        <span className="ml-2 text-xs text-drift-danger">
                          <AlertTriangle size={11} className="inline mr-1" />
                          drift
                        </span>
                      )}
                      {step.is_recovery && (
                        <span className="ml-2 text-xs text-drift-ok">
                          <TrendingDown size={11} className="inline mr-1" />
                          recovered
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <ScoreBadge score={step.per_step_score} threshold={threshold} />
                    {expandedStep === i
                      ? <ChevronUp size={14} className="text-drift-subtle" />
                      : <ChevronDown size={14} className="text-drift-subtle" />}
                  </div>
                </button>
                {expandedStep === i && (
                  <div className="px-4 pb-4 space-y-3 border-t border-drift-border/50 pt-3 fade-in">
                    <div>
                      <div className="text-xs text-drift-subtle uppercase tracking-widest mb-1 font-semibold">Input</div>
                      <p className="text-xs font-mono text-drift-text bg-drift-surface rounded-lg p-3 leading-relaxed">
                        {step.tool_input}
                      </p>
                    </div>
                    <div>
                      <div className="text-xs text-drift-subtle uppercase tracking-widest mb-1 font-semibold">Output</div>
                      <p className="text-xs font-mono text-drift-text bg-drift-surface rounded-lg p-3 leading-relaxed">
                        {step.tool_output}
                      </p>
                    </div>
                    <div className="flex gap-4 text-xs text-drift-subtle font-mono">
                      <span>per-step: <span className="text-drift-text">{step.per_step_score}</span></span>
                      <span>trajectory: <span className="text-drift-text">{step.trajectory_score}</span></span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Final answer */}
      {run.final_answer && (
        <div className="bg-drift-surface border border-drift-border rounded-2xl p-6">
          <h3 className="font-display font-semibold text-sm uppercase tracking-widest text-drift-subtle mb-4">
            Agent Final Answer
          </h3>
          <p className="text-sm text-drift-text leading-relaxed font-mono whitespace-pre-wrap">
            {run.final_answer}
          </p>
        </div>
      )}
    </div>
  )
}
