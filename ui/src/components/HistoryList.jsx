import { useEffect, useState } from 'react'
import { fetchSessions } from '../api'

const DIFFICULTY_COLOR = {
  Easy: '#10b981',
  Medium: '#f59e0b',
  Hard: '#ef4444',
}

function Badge({ label, color }) {
  return (
    <span className="badge" style={{ color, background: color + '18', borderColor: color + '40' }}>
      {label}
    </span>
  )
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export default function HistoryList({ onSelect }) {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hideFailed, setHideFailed] = useState(false)

  useEffect(() => {
    fetchSessions()
      .then(setSessions)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="history-empty">
        <div className="spinner" />
        <p>Loading sessions…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="history-empty">
        <p className="error-message">Failed to load sessions: {error}</p>
      </div>
    )
  }

  if (sessions.length === 0) {
    return (
      <div className="history-empty">
        <div className="history-empty-icon">📋</div>
        <h2>No sessions yet</h2>
        <p>Generate your first interview to see it here.</p>
      </div>
    )
  }

  const visible = hideFailed ? sessions.filter((s) => !s.failed) : sessions

  return (
    <div className="history-list">
      <div className="history-toolbar">
        <label className="history-filter-toggle">
          <input
            type="checkbox"
            checked={hideFailed}
            onChange={(e) => setHideFailed(e.target.checked)}
          />
          Hide failed runs
        </label>
      </div>
      <div className="history-table-wrapper">
        <table className="history-table">
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Date</th>
              <th>Difficulty</th>
              <th>Questions</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((s) => (
              <tr key={s.id} className={`history-row${s.failed ? ' history-row--failed' : ''}`} onClick={() => onSelect(s.id)} title={s.failed && s.error ? s.error : undefined}>
                <td className="history-candidate">
                  {s.candidate_name || <span className="text-muted">Unknown</span>}
                  {s.failed && (
                    <span className="badge" title={s.error || undefined} style={{ color: '#ef4444', background: '#ef444418', borderColor: '#ef444440', marginLeft: 8 }}>
                      Failed{s.error ? ' ⓘ' : ''}
                    </span>
                  )}
                </td>
                <td className="text-muted">{formatDate(s.created_at)}</td>
                <td>
                  {s.resolved_difficulty ? (
                    <Badge
                      label={s.resolved_difficulty}
                      color={DIFFICULTY_COLOR[s.resolved_difficulty] || '#64748b'}
                    />
                  ) : '—'}
                </td>
                <td>{s.total_questions ?? '—'}</td>
                <td>{s.estimated_duration_minutes ? `~${s.estimated_duration_minutes} min` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
