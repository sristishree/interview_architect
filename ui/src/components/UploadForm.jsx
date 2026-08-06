import { useState, useRef } from 'react'
import { submitInterview } from '../api'

const DIFFICULTIES = [
  { value: '', label: 'Auto-detect' },
  { value: 'Easy', label: 'Easy' },
  { value: 'Medium', label: 'Medium' },
  { value: 'Hard', label: 'Hard' },
]

export default function UploadForm({ onRunStarted, onError }) {
  const [file, setFile] = useState(null)
  const [difficulty, setDifficulty] = useState('')
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef()

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  function handleDragOver(e) {
    e.preventDefault()
    setDragging(true)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    try {
      const info = await submitInterview(file, null, difficulty || null)
      onRunStarted(info)
    } catch (err) {
      onError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <div
        className={`drop-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          style={{ display: 'none' }}
          onChange={(e) => setFile(e.target.files[0] || null)}
        />
        {file ? (
          <div className="file-info">
            <span className="file-icon">📄</span>
            <span className="file-name">{file.name}</span>
            <span className="file-hint">Click to change</span>
          </div>
        ) : (
          <div className="drop-prompt">
            <span className="upload-icon">↑</span>
            <span className="drop-label">Drop your resume here or click to browse</span>
            <span className="drop-hint">PDF, DOCX, or TXT</span>
          </div>
        )}
      </div>

      <div className="form-row">
        <label className="field-label">
          Difficulty
          <select
            className="field-select"
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
          >
            {DIFFICULTIES.map((d) => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>
        </label>
      </div>

      <button
        type="submit"
        className="btn-primary"
        disabled={!file || loading}
      >
        {loading ? 'Submitting…' : 'Generate Interview'}
      </button>
    </form>
  )
}
