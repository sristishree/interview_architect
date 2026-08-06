import { useEffect, useState, useRef } from 'react'
import { pollStatus } from '../api'

const POLL_MS = 3000

const STATUS_TEXT = {
  pending: 'Queued — waiting to start',
  running: 'Generating your interview — this takes 30–60s',
  success: 'Done!',
  error: 'Failed',
}

export default function StatusPoller({ runInfo, onDone, onError }) {
  const [status, setStatus] = useState(runInfo.status || 'pending')
  const [tick, setTick] = useState(0)
  const doneRef = useRef(false)

  useEffect(() => {
    if (doneRef.current) return
    if (status === 'success' || status === 'error') return

    const timer = setTimeout(async () => {
      try {
        const data = await pollStatus(runInfo.thread_id, runInfo.run_id)
        setStatus(data.status)
        if (data.status === 'success') {
          doneRef.current = true
          onDone(data.result)
        } else if (data.status === 'error') {
          doneRef.current = true
          onError(data.error || 'Run failed')
        } else {
          setTick((t) => t + 1)
        }
      } catch (err) {
        doneRef.current = true
        onError(err.message)
      }
    }, POLL_MS)

    return () => clearTimeout(timer)
  }, [status, tick, runInfo, onDone, onError])

  return (
    <div className="status-card">
      <div className="spinner" />
      <p className="status-text">{STATUS_TEXT[status] || status}</p>
      <p className="status-hint">
        Parsing resume → Extracting profile → Planning → Retrieving questions → Curating
      </p>
    </div>
  )
}
