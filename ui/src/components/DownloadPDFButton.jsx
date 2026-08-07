import { PDFDownloadLink } from '@react-pdf/renderer'
import InterviewPDF from './InterviewPDF'

export default function DownloadPDFButton({ result }) {
  const { interview_set, candidate_profile } = result
  const filename = `interview-${(interview_set.candidate_name || 'set')
    .toLowerCase()
    .replace(/\s+/g, '-')}.pdf`

  return (
    <PDFDownloadLink
      document={<InterviewPDF interview_set={interview_set} candidate_profile={candidate_profile} />}
      fileName={filename}
    >
      {({ loading }) => (
        <button className="btn-secondary" disabled={loading}>
          {loading ? 'Preparing…' : '↓ Download PDF'}
        </button>
      )}
    </PDFDownloadLink>
  )
}
