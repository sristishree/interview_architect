import { useEffect, useState } from 'react'
import { fetchSession } from '../api'
import InterviewResults from './InterviewResults'

export default function SessionDetail({ sessionId, onBack }) {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchSession(sessionId)
      .then(setSession)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [sessionId])

  if (loading) {
    return (
      <div className="history-empty">
        <div className="spinner" />
        <p>Loading session…</p>
      </div>
    )
  }

  if (error || !session || !session.interview_set) {
    const reason = error || session?.error || (!session ? 'Session not found' : 'Run failed before completing.')
    return (
      <div className="history-empty">
        <p style={{ fontWeight: 600, marginBottom: 8 }}>This run did not complete</p>
        <p className="error-message">{reason}</p>
        <button className="btn-secondary" style={{ marginTop: 16 }} onClick={onBack}>
          ← Back
        </button>
      </div>
    )
  }

  // Shape the session data to match what InterviewResults expects
  const result = {
    interview_set: session.interview_set,
    candidate_profile: session.candidate_profile,
    interview_plan: session.interview_plan,
  }

  return (
    <div style={{ width: '100%', maxWidth: 760 }}>
      <InterviewResults result={result} onReset={onBack} resetLabel="← Back to History" />
    </div>
  )
}
