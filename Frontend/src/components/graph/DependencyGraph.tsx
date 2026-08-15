import { useRef, useEffect, useCallback } from 'react'
import type { System, Dependency } from '../../types/api'
import { GraphNode, NODE_W, NODE_H } from './GraphNode'
import { GraphEdge } from './GraphEdge'
import { useStore } from '../../store/experimentStore'

interface NodePosition {
  id: string
  x: number
  y: number
}

// ── Layered layout ─────────────────────────────────────────────────────────────
// Groups nodes into layers based on topological depth (longest path from root).
function computeLayout(system: System, canvasW: number, canvasH: number): NodePosition[] {
  const inDegree: Record<string, number> = {}
  const children: Record<string, string[]> = {}

  for (const n of system.nodes) {
    inDegree[n.id] = 0
    children[n.id] = []
  }

  for (const dep of system.dependencies) {
    inDegree[dep.target] = (inDegree[dep.target] ?? 0) + 1
    children[dep.source].push(dep.target)
  }

  // BFS to assign depth layers
  const depth: Record<string, number> = {}
  const queue: string[] = []

  for (const id of Object.keys(inDegree)) {
    if (inDegree[id] === 0) {
      depth[id] = 0
      queue.push(id)
    }
  }

  while (queue.length) {
    const cur = queue.shift()!
    for (const child of children[cur]) {
      depth[child] = Math.max(depth[child] ?? 0, (depth[cur] ?? 0) + 1)
      queue.push(child)
    }
  }

  // Assign any remaining nodes depth 0
  for (const n of system.nodes) {
    if (depth[n.id] === undefined) depth[n.id] = 0
  }

  // Group by depth
  const layers: Record<number, string[]> = {}
  for (const [id, d] of Object.entries(depth)) {
    if (!layers[d]) layers[d] = []
    layers[d].push(id)
  }

  const maxDepth = Math.max(...Object.keys(layers).map(Number))
  const positions: NodePosition[] = []

  const PAD_X = 80
  const totalLayers = maxDepth + 1
  const layerStepX = (canvasW - PAD_X * 2) / Math.max(totalLayers - 1, 1)

  for (const [dStr, ids] of Object.entries(layers)) {
    const d = Number(dStr)
    const x = PAD_X + d * layerStepX
    const count = ids.length
    const totalHeight = (count - 1) * (NODE_H + 30)
    const startY = canvasH / 2 - totalHeight / 2

    ids.forEach((id, i) => {
      positions.push({ id, x, y: startY + i * (NODE_H + 30) })
    })
  }

  return positions
}

// ── Edge mid-points clipped to node borders ────────────────────────────────────
function edgeEndpoints(
  from: NodePosition,
  to: NodePosition,
): { x1: number; y1: number; x2: number; y2: number } {
  return {
    x1: from.x + NODE_W / 2,
    y1: from.y,
    x2: to.x - NODE_W / 2,
    y2: to.y,
  }
}

export function DependencyGraph() {
  const svgRef = useRef<SVGSVGElement>(null)
  const { system, selectedNodeId, nodeStates, selectNode, phase, lastResult } = useStore()

  const [dims, setDims] = React.useState({ w: 800, h: 600 })

  // Measure actual container size
  useEffect(() => {
    const el = svgRef.current?.parentElement
    if (!el) return
    const obs = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      setDims({ w: width, h: height })
    })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  const positions = computeLayout(system, dims.w, dims.h)
  const posMap = Object.fromEntries(positions.map((p) => [p.id, p]))

  // Which nodes are affected in the current result?
  const affectedSet = new Set(lastResult?.run.affected_nodes ?? [])
  const targetNode = lastResult?.run.experiment_id
    ? lastResult.events.find((e) => e.event_type === 'failure_injected')?.node_id
    : null

  const handleNodeClick = useCallback(
    (id: string) => {
      if (phase === 'running' || phase === 'propagating') return
      selectNode(selectedNodeId === id ? null : id)
    },
    [phase, selectNode, selectedNodeId],
  )

  return (
    <svg ref={svgRef} className="graph-svg">
      <defs>
        <marker
          id="arrowhead"
          markerWidth="8"
          markerHeight="8"
          refX="6"
          refY="3"
          orient="auto"
        >
          <path d="M0,0 L0,6 L8,3 z" fill="var(--border-bright)" />
        </marker>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Grid dots */}
      <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
        <circle cx="1" cy="1" r="0.8" fill="var(--border)" />
      </pattern>
      <rect width="100%" height="100%" fill="url(#grid)" />

      {/* Edges — rendered below nodes */}
      {system.dependencies.map((dep: Dependency) => {
        const from = posMap[dep.source]
        const to = posMap[dep.target]
        if (!from || !to) return null

        const isActive =
          phase === 'done' &&
          affectedSet.has(dep.target) &&
          (dep.source === targetNode || affectedSet.has(dep.source))

        const isDimmed =
          phase === 'done' &&
          !isActive &&
          selectedNodeId === null

        const { x1, y1, x2, y2 } = edgeEndpoints(from, to)

        return (
          <GraphEdge
            key={`${dep.source}→${dep.target}`}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            active={isActive}
            dimmed={isDimmed}
          />
        )
      })}

      {/* Nodes */}
      {positions.map(({ id, x, y }) => {
        const node = system.nodes.find((n) => n.id === id)
        if (!node) return null
        const vState = nodeStates[id]

        return (
          <GraphNode
            key={id}
            id={id}
            x={x}
            y={y}
            label={node.name}
            nodeType={node.node_type}
            status={vState?.status ?? 'healthy'}
            selected={selectedNodeId === id}
            highlighted={vState?.highlighted ?? false}
            animating={vState?.animating ?? false}
            onClick={handleNodeClick}
          />
        )
      })}

      {/* Experiment phase overlay text */}
      {phase === 'running' && (
        <text
          x={dims.w / 2}
          y={dims.h - 20}
          textAnchor="middle"
          fontSize={11}
          fill="var(--accent)"
          letterSpacing="0.1em"
          fontWeight="600"
        >
          SIMULATING EXPERIMENT…
        </text>
      )}
    </svg>
  )
}

// Add React import for useState
import React from 'react'
