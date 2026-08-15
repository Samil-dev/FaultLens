import type { NodeStatus, RiskLevel, ResilienceRating } from '../../types/api'

type BadgeVariant = NodeStatus | RiskLevel | ResilienceRating

const DOT_COLOR: Record<BadgeVariant, string> = {
  healthy:   'var(--color-healthy)',
  degraded:  'var(--color-degraded)',
  failed:    'var(--color-failed)',
  recovering:'var(--color-recovering)',
  low:       'var(--risk-low)',
  moderate:  'var(--risk-moderate)',
  high:      'var(--risk-high)',
  critical:  'var(--risk-critical)',
  excellent: 'var(--rating-excellent)',
  good:      'var(--rating-good)',
  poor:      'var(--rating-poor)',
}

interface Props {
  variant: BadgeVariant
  label?: string
  dot?: boolean
}

export function StatusBadge({ variant, label, dot = true }: Props) {
  const text = label ?? variant
  return (
    <span className={`status-badge badge-${variant}`}>
      {dot && (
        <span
          className="status-dot"
          style={{ background: DOT_COLOR[variant] ?? 'var(--text-muted)' }}
        />
      )}
      {text}
    </span>
  )
}
