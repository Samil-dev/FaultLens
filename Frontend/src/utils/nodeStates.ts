import type { ExperimentRunData, NodeStatus, System } from '../types/api'

export interface NodeVisualState {
  status: NodeStatus
  highlighted: boolean
  animating: boolean
}

export function buildHealthyNodeStates(system: System): Record<string, NodeVisualState> {
  const states: Record<string, NodeVisualState> = {}
  for (const node of system.nodes) {
    states[node.id] = { status: node.status as NodeStatus, highlighted: false, animating: false }
  }
  return states
}

/**
 * The node states a system settles into once `result` has fully played out —
 * i.e. the exact final frame of ExperimentModal's live propagation
 * animation. Used to reconstruct that same visual state instantly when
 * jumping to a past result from History, so reviewing history looks like
 * looking at a freshly-completed run rather than an empty/stale graph.
 *
 * Precedence matches the live animation exactly: every recovery is applied
 * generically first (recovered -> healthy, otherwise -> failed), then the
 * target node is forced back to its real outcome (failed for service_down,
 * degraded for every other type) — the simulated failure ends, but the
 * target doesn't just snap back to a plain healthy dot.
 */
export function computeSettledNodeStates(
  system: System,
  result: ExperimentRunData,
): Record<string, NodeVisualState> {
  const states = buildHealthyNodeStates(system)

  for (const recovery of result.run.recoveries) {
    if (!states[recovery.node_id]) continue
    states[recovery.node_id] = recovery.recovery_status === 'recovered'
      ? { status: 'healthy', highlighted: false, animating: false }
      : { status: 'failed', highlighted: true, animating: false }
  }

  const targetFinalStatus: NodeStatus = result.run.type === 'service_down' ? 'failed' : 'degraded'
  if (states[result.run.target_node]) {
    states[result.run.target_node] = { status: targetFinalStatus, highlighted: true, animating: false }
  }

  return states
}
