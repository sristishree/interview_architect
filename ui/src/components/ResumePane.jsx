import { useEffect, useRef, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

function PdfViewer({ url }) {
  const [numPages, setNumPages] = useState(null)
  const [error, setError] = useState(null)
  const containerRef = useRef(null)
  const [width, setWidth] = useState(null)

  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => {
      setWidth(Math.floor(entry.contentRect.width) - 32)
    })
    if (containerRef.current) observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  if (error) return <p className="resume-viewer-error">{error}</p>

  return (
    <div className="resume-pdf-viewer" ref={containerRef}>
      <Document
        file={url}
        onLoadSuccess={({ numPages }) => setNumPages(numPages)}
        onLoadError={(e) => setError(`Failed to load PDF: ${e.message}`)}
        loading={<div className="resume-viewer-loading"><div className="spinner" /></div>}
      >
        {numPages && Array.from({ length: numPages }, (_, i) => (
          <div key={i} className="resume-pdf-page">
            <Page
              pageNumber={i + 1}
              width={width || undefined}
              renderTextLayer={true}
              renderAnnotationLayer={false}
            />
          </div>
        ))}
      </Document>
    </div>
  )
}

function TextViewer({ url }) {
  const [text, setText] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`)
        return r.text()
      })
      .then(setText)
      .catch((e) => setError(e.message))
  }, [url])

  if (error) return <p className="resume-viewer-error">Failed to load resume: {error}</p>
  if (text === null) return <div className="resume-viewer-loading"><div className="spinner" /></div>
  return <pre className="resume-viewer-text">{text}</pre>
}

export default function ResumePane({ sessionId, resumePath }) {
  const isPdf = resumePath?.toLowerCase().endsWith('.pdf')
  const url = `/sessions/${sessionId}/resume`

  return (
    <div className="resume-viewer">
      {isPdf ? <PdfViewer url={url} /> : <TextViewer url={url} />}
    </div>
  )
}
