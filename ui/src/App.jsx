import { useState, useCallback } from 'react'
import UploadForm from './components/UploadForm'
import JobCard from './components/JobCard'
import ErrorBoundary from './components/ErrorBoundary'
import HistoryList from './components/HistoryList'
import SessionDetail from './components/SessionDetail'

export default function App() {
  const [page, setPage] = useState('generate')
  const [jobs, setJobs] = useState([])
  const [selectedSessionId, setSelectedSessionId] = useState(null)

  const addJob = useCallback((info, filename) => {
    setJobs((prev) => [
      {
        id: crypto.randomUUID(),
        thread_id: info.thread_id,
        run_id: info.run_id,
        status: 'running',
        filename,
        result: null,
        error: null,
      },
      ...prev,
    ])
  }, [])

  const updateJob = useCallback((id, updates) => {
    setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, ...updates } : j)))
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
      </header>

      <main className="app-main">
        {page === 'generate' && (
          <div className="generate-page">
            <UploadForm onRunStarted={addJob} />
            {jobs.length > 0 && (
              <div className="jobs-list">
                {jobs.map((job) => (
                  <ErrorBoundary key={job.id}>
                    <JobCard job={job} onUpdate={updateJob} />
                  </ErrorBoundary>
                ))}
              </div>
            )}
          </div>
        )}

        {page === 'history' && !selectedSessionId && (
          <HistoryList onSelect={setSelectedSessionId} />
        )}

        {page === 'history' && selectedSessionId && (
          <SessionDetail
            sessionId={selectedSessionId}
            onBack={() => setSelectedSessionId(null)}
          />
        )}
      </main>
    </div>
  )
}
