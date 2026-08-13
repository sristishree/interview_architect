import { useState, useRef } from 'react'
import { submitInterview } from '../api'

const DIFFICULTIES = [
  { value: '', label: 'Auto-detect' },
  { value: 'Easy', label: 'Easy' },
  { value: 'Medium', label: 'Medium' },
  { value: 'Hard', label: 'Hard' },
]

const SECTIONS = [
  { value: 'work_experience', label: 'Work Experience' },
  { value: 'projects', label: 'Projects' },
  { value: 'skills', label: 'Skills' },
]

const QUESTION_TYPES = [
  { value: 'design', label: 'Design' },
  { value: 'implementation', label: 'Implementation' },
  { value: 'theory', label: 'Theory' },
  { value: 'optimization', label: 'Optimization' },
  { value: 'behavioral', label: 'Behavioral' },
  { value: 'case_study', label: 'Case Study' },
]

export default function UploadForm({ onRunStarted }) {
  const [file, setFile] = useState(null)
  const [difficulty, setDifficulty] = useState('')
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef()

  // Mode
  const [mode, setMode] = useState('full')

  // Full interview
  const [fullCount, setFullCount] = useState('')

  // Focused interview
  const [section, setSection] = useState('work_experience')
  const [selectedTypes, setSelectedTypes] = useState([])
  const [modifier, setModifier] = useState('')
  const [focusCount, setFocusCount] = useState(10)

  function toggleType(value) {
    setSelectedTypes((prev) =>
      prev.includes(value) ? prev.filter((t) => t !== value) : [...prev, value]
    )
  }

  function handleDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (!f) return
    const ext = f.name.split('.').pop().toLowerCase()
    if (!['pdf', 'docx', 'txt'].includes(ext)) {
      setError('Only PDF, DOCX, or TXT files are supported.')
      return
    }
    setFile(f)
    setError(null)
  }

  function handleDragOver(e) {
    e.preventDefault()
    e.stopPropagation()
  }

  function handleDragEnter(e) {
    e.preventDefault()
    e.stopPropagation()
    setDragging(true)
  }

  function handleDragLeave(e) {
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setDragging(false)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return

    let focusConfig = null
    let questionCountOverride = null

    if (mode === 'focused') {
      focusConfig = {
        section,
        question_count: focusCount,
        question_types: selectedTypes.length > 0 ? selectedTypes : null,
        modifier: modifier.trim() || null,
      }
    } else if (fullCount !== '') {
      questionCountOverride = parseInt(fullCount, 10)
    }

    setLoading(true)
    setError(null)
    try {
      const info = await submitInterview(file, null, difficulty || null, focusConfig, questionCountOverride)
      onRunStarted(info, file.name)
      setFile(null)
      setDifficulty('')
      setFullCount('')
      setMode('full')
      setSection('work_experience')
      setSelectedTypes([])
      setModifier('')
      setFocusCount(10)
      if (inputRef.current) inputRef.current.value = ''
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <div
        className={`drop-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          style={{ display: 'none' }}
          onChange={(e) => { setFile(e.target.files[0] || null); setError(null) }}
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

      <div className="mode-toggle">
        <button
          type="button"
          className={`mode-tab ${mode === 'full' ? 'active' : ''}`}
          onClick={() => setMode('full')}
        >
          Full Interview
        </button>
        <button
          type="button"
          className={`mode-tab ${mode === 'focused' ? 'active' : ''}`}
          onClick={() => setMode('focused')}
        >
          Focused Interview
        </button>
      </div>

      {mode === 'full' && (
        <div className="count-field">
          <div className="field-label">
            Question Count
            <div className="count-slider-row">
              <span className="count-range-label">5</span>
              <input
                type="range"
                className="count-slider"
                min={5}
                max={30}
                value={fullCount === '' ? 18 : fullCount}
                onChange={(e) => setFullCount(e.target.value)}
              />
              <span className="count-range-label">30</span>
              <span className="count-value">
                {fullCount === '' ? <span className="count-auto">auto</span> : fullCount}
              </span>
              {fullCount !== '' && (
                <button type="button" className="count-reset" onClick={() => setFullCount('')}>
                  reset
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {mode === 'focused' && (
        <div className="focus-fields">
          <label className="field-label">
            Section
            <select
              className="field-select"
              value={section}
              onChange={(e) => setSection(e.target.value)}
            >
              {SECTIONS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </label>

          <div className="field-label">
            Question Types <span className="field-hint-text">(optional — all types if none selected)</span>
            <div className="type-multiselect">
              {QUESTION_TYPES.map((t) => (
                <span
                  key={t.value}
                  className={`type-chip ${selectedTypes.includes(t.value) ? 'selected' : ''}`}
                  onClick={() => toggleType(t.value)}
                >
                  {t.label}
                </span>
              ))}
            </div>
          </div>

          <label className="field-label">
            Modifier <span className="field-hint-text">(optional)</span>
            <textarea
              className="modifier-input"
              rows={2}
              placeholder="e.g. focus on system design aspects"
              value={modifier}
              onChange={(e) => setModifier(e.target.value)}
            />
          </label>

          <div className="field-label">
            Question Count
            <div className="count-slider-row">
              <span className="count-range-label">5</span>
              <input
                type="range"
                className="count-slider"
                min={5}
                max={30}
                value={focusCount}
                onChange={(e) => setFocusCount(Number(e.target.value))}
              />
              <span className="count-range-label">30</span>
              <span className="count-value">{focusCount}</span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="form-error">{error}</p>}

      <button type="submit" className="btn-primary" disabled={!file || loading}>
        {loading ? 'Submitting…' : 'Generate Interview'}
      </button>
    </form>
  )
}
