export async function fetchSessions() {
  const res = await fetch('/sessions', { signal: AbortSignal.timeout(10_000) })
  if (!res.ok) throw new Error(`Server error ${res.status}`)
  return res.json()
}

export async function fetchSession(id) {
  const res = await fetch(`/sessions/${id}`)
  if (!res.ok) throw new Error('Session not found')
  return res.json()
}

export async function cancelInterview(threadId, runId) {
  await fetch(`/interview/${threadId}/${runId}`, { method: 'DELETE' })
}

export async function submitInterview(file, resumePath, difficultyOverride, focusConfig, questionCountOverride) {
  const form = new FormData()
  if (file) form.append('file', file)
  if (resumePath) form.append('resume_path', resumePath)
  if (difficultyOverride) form.append('difficulty_override', difficultyOverride)
  if (focusConfig) form.append('focus_config', JSON.stringify(focusConfig))
  if (questionCountOverride != null) form.append('question_count_override', String(questionCountOverride))

  const res = await fetch('/interview', { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export async function pollStatus(threadId, runId) {
  const res = await fetch(`/interview/${threadId}/${runId}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}
