import type { KeyboardEvent } from 'react'
import type { NodeStatus } from '../../types/api'

interface Props {
  id: string
  x: number
  y: number
  label: string
  nodeType: string
  status: NodeStatus
  selected: boolean
  highlighted: boolean
  animating: boolean
  onClick: (id: string) => void
}

const STATUS_COLOR: Record<NodeStatus, string> = {
  healthy:    '#22C55E',
  degraded:   '#F59E0B',
  failed:     '#EF4444',
  recovering: '#38BDF8',
}

const NODE_TYPE_ICON: Record<string, string> = {
  gateway:  '⬡',
  service:  '◈',
  database: '⛁',
  cache:    '◎',
  queue:    '⊞',
}

const NODE_W = 120
const NODE_H = 52

export { NODE_W, NODE_H }

export function GraphNode({
  id,
  x,
  y,
  label,
  nodeType,
  status,
  selected,
  highlighted,
  animating,
  onClick,
}: Props) {
  const color = STATUS_COLOR[status] ?? '#94A3B8'
  const icon = NODE_TYPE_ICON[nodeType] ?? '◆'
  const rx = x - NODE_W / 2
  const ry = y - NODE_H / 2

  function handleKeyDown(e: KeyboardEvent<SVGGElement>) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onClick(id)
    }
  }

  return (
    <g
      className="graph-node-group"
      transform={`translate(${rx},${ry})`}
      onClick={() => onClick(id)}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      aria-label={`${label}, ${nodeType}, status ${status}`}
    >
      <title>{`${label} (${nodeType}) — ${status}`}</title>

      {/* Pulse ring when animating */}
      {animating && (
        <circle
          cx={NODE_W / 2}
          cy={NODE_H / 2}
          r={28}
          fill="none"
          stroke={color}
          strokeWidth={1.5}
          opacity={0}
        >
          <animate
            attributeName="r"
            from="28" to="46"
            dur="1s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            from="0.7" to="0"
            dur="1s"
            repeatCount="indefinite"
          />
        </circle>
      )}

      {/* Selection glow */}
      {selected && (
        <rect
          x={-3} y={-3}
          width={NODE_W + 6}
          height={NODE_H + 6}
          rx={9}
          fill="none"
          stroke="var(--accent)"
          strokeWidth={1.5}
          opacity={0.6}
        />
      )}

      {/* Highlight border */}
      {highlighted && !selected && (
        <rect
          x={-2} y={-2}
          width={NODE_W + 4}
          height={NODE_H + 4}
          rx={8}
          fill="none"
          stroke={color}
          strokeWidth={1}
          opacity={0.5}
        />
      )}

      {/* Node body */}
      <rect
        className="graph-node-body"
        width={NODE_W}
        height={NODE_H}
        rx={6}
        fill="var(--bg-panel)"
        stroke={selected ? 'var(--accent)' : highlighted ? color : 'var(--border)'}
        strokeWidth={selected ? 1.5 : 1}
        style={{ transition: 'stroke 0.2s, fill 0.2s' }}
      />

      {/* Status bar on left edge */}
      <rect
        x={0} y={0}
        width={3}
        height={NODE_H}
        rx={6}
        fill={color}
        style={{ transition: 'fill 0.3s' }}
      />

      {/* Icon */}
      <text
        x={14}
        y={NODE_H / 2 + 1}
        fontSize={13}
        fill={color}
        dominantBaseline="middle"
        textAnchor="middle"
        style={{ transition: 'fill 0.3s' }}
      >
        {icon}
      </text>

      {/* Node name */}
      <text
        x={24}
        y={NODE_H / 2 - 7}
        fontSize={11}
        fontWeight="600"
        fill="var(--text-primary)"
        dominantBaseline="middle"
      >
        {label.length > 14 ? label.slice(0, 13) + '…' : label}
      </text>

      {/* Node type */}
      <text
        x={24}
        y={NODE_H / 2 + 7}
        fontSize={9.5}
        fill="var(--text-muted)"
        dominantBaseline="middle"
        letterSpacing="0.04em"
        fontWeight="500"
      >
        {nodeType.toUpperCase()}
      </text>

      {/* Status dot */}
      <circle
        cx={NODE_W - 10}
        cy={10}
        r={4}
        fill={color}
        style={{ transition: 'fill 0.3s' }}
      >
        {animating && (
          <animate
            attributeName="opacity"
            values="1;0.2;1"
            dur="0.8s"
            repeatCount="indefinite"
          />
        )}
      </circle>
    </g>
  )
}
