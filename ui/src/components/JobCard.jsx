import { useEffect, useRef, useState } from 'react'
import { cancelInterview } from '../api'
import InterviewResults from './InterviewResults'

const ALL_NODES = [
  { key: 'extract_text',       label: 'Extracting resume text' },
  { key: 'build_profile',      label: 'Building candidate profile' },
  { key: 'plan_interview',     label: 'Planning interview' },
  { key: 'retrieve_questions', label: 'Retrieving questions' },
  { key: 'curate_interview',   label: 'Curating final question set' },
]

function RunningCard({ job }) {
  const [completed, setCompleted] = useState(new Set())
  const [activeNode, setActiveNode] = useState(null)
  const { onDone, onError, onCancel } = job._handlers
  const esRef = useRef(null)
  const doneRef = useRef(false)

  useEffect(() => {
    const es = new EventSource(`/interview/${job.thread_id}/${job.run_id}/stream`)
    esRef.current = es

    es.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'progress') {
        setActiveNode(msg.node)
        setCompleted((prev) => new Set([...prev, msg.node]))
      } else if (msg.type === 'done') {
        doneRef.current = true
        es.close()
        onDone(msg.result)
      } else if (msg.type === 'error') {
        doneRef.current = true
        es.close()
        onError(msg.message)
      }
    }

    es.onerror = () => {
      if (!doneRef.current) {
        doneRef.current = true
        es.close()
        onError('Lost connection to server')
      }
    }

    return () => { if (!doneRef.current) es.close() }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleCancel() {
    doneRef.current = true
    esRef.current?.close()
    await cancelInterview(job.thread_id, job.run_id).catch(() => {})
    onCancel()
  }

  return (
    <div className="job-card job-card--running">
      <div className="job-card-header">
        <span className="job-filename">📄 {job.filename}</span>
        <div className="job-card-header-right">
          <span className="job-status-badge running">
            <span className="job-spinner" /> Generating…
          </span>
          <button className="btn-cancel" onClick={handleCancel}>Cancel</button>
        </div>
      </div>
      <div className="progress-steps">
        {ALL_NODES.map(({ key, label }) => {
          const isDone = completed.has(key)
          const isActive = activeNode === key && !isDone
          return (
            <div key={key} className={`progress-step ${isDone ? 'done' : isActive ? 'active' : ''}`}>
              <span className="step-dot">{isDone ? '✓' : isActive ? '●' : '○'}</span>
              <span className="step-label">{label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function DoneCard({ job }) {
  const [expanded, setExpanded] = useState(true)
  const { interview_set } = job.result

  return (
    <div className="job-card job-card--done">
      <div className="job-card-header" onClick={() => setExpanded((e) => !e)}>
        <span className="job-filename">{job.filename}</span>
        <div className="job-card-header-right">
          <span className="job-status-badge done">✓ Done</span>
          <span className="job-toggle">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>
      {expanded && (
        <div className="job-card-body">
          <InterviewResults result={job.result} />
        </div>
      )}
    </div>
  )
}

function ErrorCard({ job }) {
  return (
    <div className="job-card job-card--error">
      <div className="job-card-header">
        <span className="job-filename">📄 {job.filename}</span>
        <span className="job-status-badge error">✕ Failed</span>
      </div>
      <p className="job-error-msg">{job.error}</p>
    </div>
  )
}

function CanceledCard({ job }) {
  return (
    <div className="job-card job-card--canceled">
      <div className="job-card-header">
        <span className="job-filename">📄 {job.filename}</span>
        <span className="job-status-badge canceled">◼ Canceled</span>
      </div>
    </div>
  )
}

export default function JobCard({ job, onUpdate }) {
  // Attach callbacks as a ref so RunningCard's closed-over effect can call them
  // without needing to re-run the effect when onUpdate changes.
  const handlersRef = useRef(null)
  handlersRef.current = {
    onDone:   (result) => onUpdate(job.id, { status: 'done',     result }),
    onError:  (error)  => onUpdate(job.id, { status: 'error',    error }),
    onCancel: ()       => onUpdate(job.id, { status: 'canceled' }),
  }

  // Pass handlers via a stable ref wrapper so RunningCard doesn't need them in deps
  const jobWithHandlers = { ...job, _handlers: handlersRef.current }

  if (job.status === 'running')  return <RunningCard job={jobWithHandlers} />
  if (job.status === 'done')     return <DoneCard job={job} />
  if (job.status === 'canceled') return <CanceledCard job={job} />
  return <ErrorCard job={job} />
}
