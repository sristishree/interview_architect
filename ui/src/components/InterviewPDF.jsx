import { Document, Page, View, Text, StyleSheet } from '@react-pdf/renderer'

const DIFFICULTY_COLOR = {
  Easy:   '#10b981',
  Medium: '#f59e0b',
  Hard:   '#ef4444',
}

const TYPE_COLOR = {
  implementation: '#3b82f6',
  theory:         '#8b5cf6',
  design:         '#f59e0b',
  behavioral:     '#10b981',
  optimization:   '#ef4444',
  case_study:     '#6366f1',
}

const s = StyleSheet.create({
  page: {
    fontFamily: 'Helvetica',
    fontSize: 10,
    color: '#1e293b',
    paddingTop: 40,
    paddingBottom: 52,
    paddingHorizontal: 48,
    backgroundColor: '#ffffff',
  },

  /* ── Header ── */
  header: {
    marginBottom: 20,
    paddingBottom: 14,
    borderBottomWidth: 2,
    borderBottomColor: '#4f46e5',
  },
  title: {
    fontSize: 18,
    fontFamily: 'Helvetica-Bold',
    color: '#1e293b',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 10,
    color: '#64748b',
    marginBottom: 10,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  statBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  statText: {
    fontSize: 8.5,
    fontFamily: 'Helvetica-Bold',
  },

  /* ── Section ── */
  section: {
    marginBottom: 14,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderLeftWidth: 3,
    borderLeftColor: '#4f46e5',
    marginBottom: 8,
  },
  sectionName: {
    fontSize: 9.5,
    fontFamily: 'Helvetica-Bold',
    color: '#1e293b',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionCount: {
    fontSize: 8,
    color: '#94a3b8',
  },

  /* ── Question ── */
  questionCard: {
    marginBottom: 10,
    paddingLeft: 12,
    borderLeftWidth: 1,
    borderLeftColor: '#e2e8f0',
  },
  questionRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 4,
  },
  questionNum: {
    fontSize: 8.5,
    color: '#94a3b8',
    fontFamily: 'Helvetica-Bold',
    minWidth: 18,
    paddingTop: 1,
  },
  questionText: {
    flex: 1,
    fontSize: 10,
    color: '#1e293b',
    lineHeight: 1.55,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 5,
    marginTop: 4,
    marginLeft: 26,
  },
  badge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 999,
    borderWidth: 1,
  },
  badgeText: {
    fontSize: 7,
    fontFamily: 'Helvetica-Bold',
  },
  followUp: {
    marginTop: 5,
    marginLeft: 26,
    padding: 8,
    backgroundColor: '#f8fafc',
    borderRadius: 4,
  },
  followUpLabel: {
    fontSize: 7.5,
    fontFamily: 'Helvetica-Bold',
    color: '#64748b',
    marginBottom: 3,
  },
  followUpText: {
    fontSize: 9,
    color: '#475569',
    lineHeight: 1.45,
  },

  /* ── Curator notes ── */
  curatorNotes: {
    marginTop: 18,
    padding: 12,
    backgroundColor: '#fffbeb',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#fde68a',
  },
  curatorLabel: {
    fontSize: 8,
    fontFamily: 'Helvetica-Bold',
    color: '#92400e',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  curatorText: {
    fontSize: 9,
    color: '#78350f',
    lineHeight: 1.55,
  },

  /* ── Footer ── */
  footer: {
    position: 'absolute',
    bottom: 24,
    left: 48,
    right: 48,
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    paddingTop: 6,
  },
  footerText: {
    fontSize: 7.5,
    color: '#94a3b8',
  },
})

function Badge({ label, color }) {
  return (
    <View style={[s.badge, { borderColor: color + '50', backgroundColor: color + '18' }]}>
      <Text style={[s.badgeText, { color }]}>{label}</Text>
    </View>
  )
}

function QuestionItem({ q, index }) {
  const diffColor = DIFFICULTY_COLOR[q.difficulty] || '#64748b'
  const typeColor = TYPE_COLOR[q.question_type] || '#64748b'
  return (
    <View style={s.questionCard}>
      <View style={s.questionRow}>
        <Text style={s.questionNum}>{index + 1}.</Text>
        <Text style={s.questionText}>{q.question}</Text>
      </View>
      <View style={s.badgeRow}>
        <Badge label={q.difficulty} color={diffColor} />
        <Badge label={q.question_type} color={typeColor} />
      </View>
      {q.follow_up && (
        <View style={s.followUp}>
          <Text style={s.followUpLabel}>Follow-up</Text>
          <Text style={s.followUpText}>{q.follow_up}</Text>
        </View>
      )}
    </View>
  )
}

export default function InterviewPDF({ interview_set, candidate_profile }) {
  const diffColor = DIFFICULTY_COLOR[interview_set.resolved_difficulty] || '#64748b'

  return (
    <Document>
      <Page size="A4" style={s.page}>

        {/* Header */}
        <View style={s.header}>
          <Text style={s.title}>Interview Set — {interview_set.candidate_name}</Text>
          {candidate_profile && (
            <Text style={s.subtitle}>
              {candidate_profile.role} · {candidate_profile.seniority} · {candidate_profile.years_of_experience} yrs
            </Text>
          )}
          <View style={s.statsRow}>
            <View style={[s.statBadge, { backgroundColor: diffColor + '18' }]}>
              <Text style={[s.statText, { color: diffColor }]}>{interview_set.resolved_difficulty}</Text>
            </View>
            <View style={[s.statBadge, { backgroundColor: '#f1f5f9' }]}>
              <Text style={[s.statText, { color: '#475569' }]}>{interview_set.total_questions} questions</Text>
            </View>
            <View style={[s.statBadge, { backgroundColor: '#f1f5f9' }]}>
              <Text style={[s.statText, { color: '#475569' }]}>~{interview_set.estimated_duration_minutes} min</Text>
            </View>
          </View>
        </View>

        {/* Sections */}
        {interview_set.sections.map((section) => (
          <View key={section.name} style={s.section}>
            <View style={s.sectionHeader}>
              <Text style={s.sectionName}>{section.name}</Text>
              <Text style={s.sectionCount}>{section.questions.length} questions</Text>
            </View>
            {section.questions.map((q, i) => (
              <QuestionItem key={q.id ?? i} q={q} index={i} />
            ))}
          </View>
        ))}

        {/* Curator notes */}
        {interview_set.curator_notes && (
          <View style={s.curatorNotes}>
            <Text style={s.curatorLabel}>Curator Notes</Text>
            <Text style={s.curatorText}>{interview_set.curator_notes}</Text>
          </View>
        )}

        {/* Footer — repeated on every page */}
        <View style={s.footer} fixed>
          <Text style={s.footerText}>Interview Architect</Text>
          <Text
            style={s.footerText}
            render={({ pageNumber, totalPages }) => `Page ${pageNumber} of ${totalPages}`}
          />
        </View>

      </Page>
    </Document>
  )
}
