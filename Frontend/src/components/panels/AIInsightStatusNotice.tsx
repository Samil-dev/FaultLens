import type { AIInsight } from '../../types/api'

const STATUS_COPY: Record<Exclude<AIInsight['status'], 'available'>, { icon: string; title: string }> = {
  not_configured: { icon: '⚙', title: 'AI provider not configured' },
  unavailable:    { icon: '🔌', title: 'AI provider temporarily unavailable' },
  error:          { icon: '⚠',  title: 'AI analysis failed' },
}

/**
 * Renders an honest, distinctly-styled notice for every AIInsight status
 * other than 'available' — never a fabricated summary. Returns null when
 * the insight is available, so callers render their own real content in
 * that case and only need to guard the non-available branch with this.
 */
export function AIInsightStatusNotice({ insight }: { insight: AIInsight }) {
  if (insight.status === 'available') return null

  const { icon, title } = STATUS_COPY[insight.status]

  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px dashed var(--border-bright)',
      borderRadius: 'var(--radius-md)',
      padding: '10px 12px',
      display: 'flex',
      gap: 8,
      alignItems: 'flex-start',
    }}>
      <span style={{ fontSize: 14, opacity: 0.7 }}>{icon}</span>
      <div>
        <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 2 }}>
          {title}
        </p>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>
          {insight.message ?? 'No further detail is available.'}
        </p>
      </div>
    </div>
  )
}
