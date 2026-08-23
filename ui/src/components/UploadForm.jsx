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

const DEFAULTS = {
  difficulty: '',
  mode: 'full',
  fullCount: '',
  section: 'work_experience',
  selectedTypes: [],
  modifier: '',
  focusCount: '',
}

export default function UploadForm({ onRunStarted }) {
  const [file, setFile] = useState(null)
  const [difficulty, setDifficulty] = useState(DEFAULTS.difficulty)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef()

  const [mode, setMode] = useState(DEFAULTS.mode)
  const [fullCount, setFullCount] = useState(DEFAULTS.fullCount)
  const [section, setSection] = useState(DEFAULTS.section)
  const [selectedTypes, setSelectedTypes] = useState(DEFAULTS.selectedTypes)
  const [modifier, setModifier] = useState(DEFAULTS.modifier)
  const [focusCount, setFocusCount] = useState(DEFAULTS.focusCount)

  function clampCount(raw, fallback) {
    const n = parseInt(raw, 10)
    if (isNaN(n)) return String(fallback)
    return String(Math.min(30, Math.max(5, n)))
  }

  function handleReset() {
    setFile(null)
    setDifficulty(DEFAULTS.difficulty)
    setMode(DEFAULTS.mode)
    setFullCount(DEFAULTS.fullCount)
    setSection(DEFAULTS.section)
    setSelectedTypes(DEFAULTS.selectedTypes)
    setModifier(DEFAULTS.modifier)
    setFocusCount(DEFAULTS.focusCount)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

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

  function handleDragOver(e) { e.preventDefault(); e.stopPropagation() }
  function handleDragEnter(e) { e.preventDefault(); e.stopPropagation(); setDragging(true) }
  function handleDragLeave(e) {
    if (!e.currentTarget.contains(e.relatedTarget)) setDragging(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return

    let focusConfig = null
    let questionCountOverride = null

    if (mode === 'focused') {
      focusConfig = {
        section,
        question_count: focusCount !== '' ? parseInt(clampCount(focusCount, 10), 10) : null,
        question_types: selectedTypes.length > 0 ? selectedTypes : null,
        modifier: modifier.trim() || null,
      }
    } else if (fullCount !== '') {
      questionCountOverride = parseInt(clampCount(fullCount, 18), 10)
    }

    setLoading(true)
    setError(null)
    try {
      const info = await submitInterview(file, null, difficulty || null, focusConfig, questionCountOverride)
      onRunStarted(info, file.name)
      // Only clear the file — settings persist for the next submission
      setFile(null)
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
            Question Count <span className="field-hint-text">(optional)</span>
            <div className="count-slider-row">
              <span className="count-range-label">5</span>
              <input
                type="range"
                className="count-slider"
                min={5}
                max={30}
                value={fullCount === '' ? 18 : clampCount(fullCount, 18)}
                onChange={(e) => setFullCount(e.target.value)}
              />
              <span className="count-range-label">30</span>
              <input
                type="number"
                className="count-number-input"
                placeholder="auto"
                value={fullCount}
                onChange={(e) => setFullCount(e.target.value)}
                onBlur={() => { if (fullCount !== '') setFullCount(clampCount(fullCount, 18)) }}
              />
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
            Question Count <span className="field-hint-text">(optional — leave blank to let the expert decide)</span>
            <div className="count-slider-row">
              <span className="count-range-label">5</span>
              <input
                type="range"
                className="count-slider"
                min={5}
                max={30}
                value={focusCount === '' ? 10 : clampCount(focusCount, 10)}
                onChange={(e) => setFocusCount(e.target.value)}
              />
              <span className="count-range-label">30</span>
              <input
                type="number"
                className="count-number-input"
                placeholder="auto"
                value={focusCount}
                onChange={(e) => setFocusCount(e.target.value)}
                onBlur={() => { if (focusCount !== '') setFocusCount(clampCount(focusCount, 10)) }}
              />
              {focusCount !== '' && (
                <button type="button" className="count-reset" onClick={() => setFocusCount('')}>
                  reset
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {error && <p className="form-error">{error}</p>}

      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={!file || loading}>
          {loading ? 'Submitting…' : 'Generate Interview'}
        </button>
        <button type="button" className="btn-reset-all" onClick={handleReset}>
          Reset
        </button>
      </div>
    </form>
  )
}
