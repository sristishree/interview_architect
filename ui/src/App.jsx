import { useState, useCallback } from 'react'
import UploadForm from './components/UploadForm'
import JobCard from './components/JobCard'
import ErrorBoundary from './components/ErrorBoundary'
import HistoryList from './components/HistoryList'
import SessionDetail from './components/SessionDetail'

const STATUS_DOT = { done: '✓', error: '✕', canceled: '◼' }
const TAB_DOT_CLASS = {
  running: 'tab-dot--running',
  done: 'tab-dot--done',
  error: 'tab-dot--error',
  canceled: 'tab-dot--canceled',
}

export default function App() {
  const [page, setPage] = useState('generate')
  const [jobs, setJobs] = useState([])
  const [activeTabId, setActiveTabId] = useState(null)
  const [selectedSessionId, setSelectedSessionId] = useState(null)

  const addJob = useCallback((info, filename) => {
    const id = crypto.randomUUID()
    setJobs((prev) => [{
      id,
      thread_id: info.thread_id,
      run_id: info.run_id,
      status: 'running',
      filename,
      result: null,
      error: null,
      notices: [],
    }, ...prev])
    setActiveTabId(id)
  }, [])

  const updateJob = useCallback((id, updates) => {
    setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, ...updates } : j)))
  }, [])

  const closeTab = useCallback((id) => {
    setJobs((prev) => {
      const idx = prev.findIndex((j) => j.id === id)
      const next = prev.filter((j) => j.id !== id)
      setActiveTabId((cur) => {
        if (cur !== id) return cur
        return next[idx]?.id ?? next[idx - 1]?.id ?? null
      })
      return next
    })
  }, [])

  function switchPage(p) {
    setPage(p)
    setSelectedSessionId(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Interview Architect</h1>
        <p>Generate a structured interview question set from a resume</p>
      </header>

      <nav className="app-nav">
        <button
          className={`nav-tab ${page === 'generate' ? 'active' : ''}`}
          onClick={() => switchPage('generate')}
        >
          Generate
        </button>
        <button
          className={`nav-tab ${page === 'history' ? 'active' : ''}`}
          onClick={() => switchPage('history')}
        >
          History
        </button>
      </nav>

      {page === 'generate' && (
        <div className="workspace">
          <aside className="config-pane">
            <UploadForm onRunStarted={addJob} />
          </aside>

          <div className="results-pane">
            {jobs.length === 0 ? (
              <div className="results-empty">
                <p>Upload a resume and click Generate — results will appear here.</p>
              </div>
            ) : (
              <>
                <div className="tab-strip" role="tablist">
                  {jobs.map((job) => (
                    <button
                      key={job.id}
                      role="tab"
                      aria-selected={activeTabId === job.id}
                      className={`tab-btn ${activeTabId === job.id ? 'active' : ''}`}
                      onClick={() => setActiveTabId(job.id)}
                    >
                      <span className={`tab-dot ${TAB_DOT_CLASS[job.status]}`}>
                        {job.status === 'running'
                          ? <span className="tab-spinner" />
                          : STATUS_DOT[job.status]}
                      </span>
                      <span className="tab-label">{job.filename}</span>
                      {job.status !== 'running' && (
                        <span
                          className="tab-close"
                          role="button"
                          aria-label="Close tab"
                          onClick={(e) => { e.stopPropagation(); closeTab(job.id) }}
                        >
                          ×
                        </span>
                      )}
                    </button>
                  ))}
                </div>

                <div className="tab-content">
                  {jobs.map((job) => (
                    <div key={job.id} className={`tab-panel${job.id !== activeTabId ? ' tab-panel--hidden' : ''}`}>
                      <ErrorBoundary>
                        <JobCard job={job} onUpdate={updateJob} />
                      </ErrorBoundary>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {page === 'history' && (
        <main className="app-main">
          {!selectedSessionId && <HistoryList onSelect={setSelectedSessionId} />}
          {selectedSessionId && (
            <SessionDetail
              sessionId={selectedSessionId}
              onBack={() => setSelectedSessionId(null)}
            />
          )}
        </main>
      )}
    </div>
  )
}
