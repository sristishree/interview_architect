import { useState } from 'react'

const TYPE_COLOR = {
  implementation: '#3b82f6',
  theory: '#8b5cf6',
  design: '#f59e0b',
  behavioral: '#10b981',
  optimization: '#ef4444',
  case_study: '#6366f1',
}

const DIFFICULTY_COLOR = {
  Easy: '#10b981',
  Medium: '#f59e0b',
  Hard: '#ef4444',
}

function Badge({ label, color }) {
  return (
    <span
      className="badge"
      style={{ color, background: color + '18', borderColor: color + '40' }}
    >
      {label}
    </span>
  )
}

function QuestionCard({ q, index }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="question-card">
      <div className="question-row" onClick={() => setOpen((o) => !o)}>
        <span className="q-num">{index + 1}</span>
        <span className="q-text">{q.question}</span>
        <div className="q-meta">
          <Badge label={q.question_type} color={TYPE_COLOR[q.question_type] || '#64748b'} />
          <Badge label={q.difficulty} color={DIFFICULTY_COLOR[q.difficulty] || '#64748b'} />
        </div>
        <span className="q-toggle">{open ? '▲' : '▼'}</span>
      </div>
      {open && q.follow_up && (
        <div className="follow-up">
          <strong>Follow-up: </strong>{q.follow_up}
        </div>
      )}
    </div>
  )
}

function SectionCard({ section }) {
  const [collapsed, setCollapsed] = useState(false)
  return (
    <div className="section-card">
      <div className="section-header" onClick={() => setCollapsed((c) => !c)}>
        <h3 className="section-name">{section.name}</h3>
        <span className="section-count">{section.questions.length} questions</span>
        <span className="s-toggle">{collapsed ? '▼' : '▲'}</span>
      </div>
      {!collapsed && (
        <div className="section-body">
          {section.questions.map((q, i) => (
            <QuestionCard key={q.id ?? i} q={q} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function InterviewResults({ result, onReset }) {
  const { interview_set, candidate_profile } = result

  return (
    <div className="results">
      <div className="results-header">
        <div className="results-meta">
          <h2 className="candidate-name">{interview_set.candidate_name}</h2>
          {candidate_profile && (
            <p className="candidate-role">
              {candidate_profile.role} · {candidate_profile.seniority} · {candidate_profile.years_of_experience} yrs
            </p>
          )}
          <div className="results-stats">
            <span>📋 {interview_set.total_questions} questions</span>
            <span>⏱ ~{interview_set.estimated_duration_minutes} min</span>
            <Badge
              label={interview_set.resolved_difficulty}
              color={DIFFICULTY_COLOR[interview_set.resolved_difficulty] || '#64748b'}
            />
          </div>
        </div>
        <button className="btn-secondary" onClick={onReset}>New Interview</button>
      </div>

      {interview_set.sections.map((s) => (
        <SectionCard key={s.name} section={s} />
      ))}

      {interview_set.curator_notes && (
        <div className="curator-notes">
          <strong>Curator notes: </strong>{interview_set.curator_notes}
        </div>
      )}
    </div>
  )
}
