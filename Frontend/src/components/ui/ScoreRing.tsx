interface Props {
  score: number       // 0–100
  size?: number       // svg width/height in px
  strokeWidth?: number
  color?: string
}

const RATING_COLOR = (score: number) => {
  if (score >= 80) return 'var(--rating-excellent)'
  if (score >= 60) return 'var(--rating-good)'
  if (score >= 40) return 'var(--rating-moderate)'
  if (score >= 20) return 'var(--rating-poor)'
  return 'var(--rating-critical)'
}

export function ScoreRing({ score, size = 80, strokeWidth = 6, color }: Props) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const filled = circumference * (score / 100)
  const ringColor = color ?? RATING_COLOR(score)
  const cx = size / 2
  const cy = size / 2

  return (
    <div className="score-ring-wrap">
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* track */}
        <circle
          cx={cx} cy={cy} r={radius}
          fill="none"
          stroke="var(--bg-elevated)"
          strokeWidth={strokeWidth}
        />
        {/* filled arc */}
        <circle
          cx={cx} cy={cy} r={radius}
          fill="none"
          stroke={ringColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference - filled}`}
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
      </svg>
      {/* centre label — positioned absolutely over the SVG */}
      <div style={{
        position: 'absolute',
        fontSize: size < 70 ? 13 : 18,
        fontWeight: 700,
        color: ringColor,
        fontVariantNumeric: 'tabular-nums',
      }}>
        {Math.round(score)}
      </div>
    </div>
  )
}
