const BASE = import.meta.env.VITE_API_URL ?? '/api'

export async function postRun({ userMessage, distractionMessage, runLabel, scenario }) {
  const res = await fetch(`${BASE}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_message: userMessage,
      distraction_message: distractionMessage || null,
      run_label: runLabel || null,
      scenario: scenario || 'lease_qa',
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Run failed')
  }
  return res.json()
}

export async function getRuns() {
  const res = await fetch(`${BASE}/runs`)
  if (!res.ok) throw new Error('Failed to fetch runs')
  return res.json()
}

export async function clearRuns() {
  const res = await fetch(`${BASE}/runs`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to clear runs')
  return res.json()
}
