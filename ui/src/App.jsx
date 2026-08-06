import { useState } from 'react'
import UploadForm from './components/UploadForm'
import StatusPoller from './components/StatusPoller'
import InterviewResults from './components/InterviewResults'

export default function App() {
  const [step, setStep] = useState('upload')
  const [runInfo, setRunInfo] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  function handleRunStarted(info) {
    setRunInfo(info)
    setStep('running')
  }

  function handleDone(res) {
    setResult(res)
    setStep('done')
  }

  function handleError(msg) {
    setError(msg)
    setStep('error')
  }

  function handleReset() {
    setStep('upload')
    setRunInfo(null)
    setResult(null)
    setError(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Interview Architect</h1>
        <p>Generate a structured interview question set from a resume</p>
      </header>

      <main className="app-main">
        {step === 'upload' && (
          <UploadForm onRunStarted={handleRunStarted} onError={handleError} />
        )}
        {step === 'running' && (
          <StatusPoller runInfo={runInfo} onDone={handleDone} onError={handleError} />
        )}
        {step === 'done' && (
          <InterviewResults result={result} onReset={handleReset} />
        )}
        {step === 'error' && (
          <div className="error-card">
            <div className="error-icon">✕</div>
            <h2>Something went wrong</h2>
            <p className="error-message">{error}</p>
            <button className="btn-primary" onClick={handleReset}>Try again</button>
          </div>
        )}
      </main>
    </div>
  )
}
