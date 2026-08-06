export async function submitInterview(file, resumePath, difficultyOverride) {
  const form = new FormData()
  if (file) form.append('file', file)
  if (resumePath) form.append('resume_path', resumePath)
  if (difficultyOverride) form.append('difficulty_override', difficultyOverride)

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
