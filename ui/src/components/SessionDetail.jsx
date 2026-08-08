import { useEffect, useState } from 'react'
import { fetchSession } from '../api'
import InterviewResults from './InterviewResults'
import ResumePane from './ResumePane'

export default function SessionDetail({ sessionId, onBack }) {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showResume, setShowResume] = useState(false)

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
        <button className="btn-secondary" style={{ marginTop: 16 }} onClick={onBack}>Back</button>
      </div>
    )
  }

  const result = {
    interview_set: session.interview_set,
    candidate_profile: session.candidate_profile,
    interview_plan: session.interview_plan,
  }

  const resumeToggle = (
    <button
      className={`btn-secondary ${showResume ? 'active' : ''}`}
      onClick={() => setShowResume((v) => !v)}
    >
      {showResume ? 'Hide Resume' : 'Show Resume'}
    </button>
  )

  return (
    <div className={`session-detail-page ${showResume ? 'has-pane' : ''}`}>
      <div className="session-detail-toolbar">
        <button className="btn-secondary" onClick={onBack}>Back to History</button>
      </div>

      <div className={`session-detail-body ${showResume ? 'with-pane' : ''}`}>
        <div className="session-detail-main">
          <InterviewResults result={result} headerAction={resumeToggle} />
        </div>
        {showResume && (
          <aside className="session-detail-aside">
            <ResumePane sessionId={sessionId} resumePath={session.resume_path} />
          </aside>
        )}
      </div>
    </div>
  )
}
