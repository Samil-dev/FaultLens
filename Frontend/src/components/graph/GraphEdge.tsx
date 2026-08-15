interface Props {
  x1: number
  y1: number
  x2: number
  y2: number
  active: boolean   // failure is propagating through this edge
  dimmed: boolean   // irrelevant during active experiment
}

export function GraphEdge({ x1, y1, x2, y2, active, dimmed }: Props) {
  // Draw a curved bezier between two nodes
  const dx = x2 - x1
  const mx = x1 + dx / 2

  const d = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`

  return (
    <g>
      {/* Shadow / glow for active edges */}
      {active && (
        <path
          d={d}
          fill="none"
          stroke="var(--color-failed)"
          strokeWidth={3}
          opacity={0.2}
        />
      )}
      <path
        d={d}
        fill="none"
        stroke={active ? 'var(--color-failed)' : dimmed ? 'var(--border)' : 'var(--border-bright)'}
        strokeWidth={active ? 1.5 : 1}
        opacity={dimmed ? 0.3 : 1}
        strokeDasharray={active ? '6 4' : undefined}
        style={{
          transition: 'stroke 0.3s, opacity 0.3s',
          animation: active ? 'dashFlow 0.6s linear infinite' : undefined,
        }}
        markerEnd={active ? undefined : 'url(#arrowhead)'}
      />
    </g>
  )
}
