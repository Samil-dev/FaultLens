import type { System } from '../types/api'

/**
 * Topology helpers computed purely from the system's own dependency list —
 * the same data already loaded into the store. Nothing here is fabricated:
 * every value is derived from the real architecture the backend returned.
 */

/** Node IDs this node directly depends on (outgoing edges). */
export function getDirectDependencies(system: System, nodeId: string): string[] {
  return system.dependencies.filter((d) => d.source === nodeId).map((d) => d.target)
}

/** Node IDs that directly depend on this node (incoming edges). */
export function getDirectDependents(system: System, nodeId: string): string[] {
  return system.dependencies.filter((d) => d.target === nodeId).map((d) => d.source)
}

/**
 * Every node that would potentially be affected if `nodeId` failed, mirroring
 * the backend's DependencyGraph.get_affected_nodes: a BFS over the reverse
 * dependency graph, returning each node exactly once, in propagation order.
 * This is a *preview* computed from topology alone — the backend's own
 * post-experiment blast radius also factors in measured metric impact, so
 * the two numbers can differ. Used before an experiment has been run.
 */
export function getPotentialAffectedNodes(system: System, nodeId: string): string[] {
  const reverseGraph = new Map<string, string[]>()
  for (const dep of system.dependencies) {
    const list = reverseGraph.get(dep.target) ?? []
    list.push(dep.source)
    reverseGraph.set(dep.target, list)
  }

  const affected: string[] = []
  const enqueued = new Set([nodeId])
  const queue = [nodeId]

  while (queue.length) {
    const current = queue.shift()!
    for (const dependent of reverseGraph.get(current) ?? []) {
      if (!enqueued.has(dependent)) {
        enqueued.add(dependent)
        affected.push(dependent)
        queue.push(dependent)
      }
    }
  }

  return affected
}

export type CriticalityTier = 'low' | 'moderate' | 'high'

/**
 * A structural criticality estimate based on how much of the system would
 * potentially be affected if this node failed — NOT a backend-computed
 * field (the backend only classifies criticality after actually running an
 * experiment, via ImpactAnalysis.critical_nodes). Always label this as a
 * topology-based estimate in the UI so it isn't confused with a measured result.
 */
export function estimateCriticality(potentialAffectedCount: number, totalNodes: number): CriticalityTier {
  if (totalNodes <= 0 || potentialAffectedCount <= 0) return 'low'
  const ratio = potentialAffectedCount / totalNodes
  if (ratio >= 0.3) return 'high'
  if (ratio > 0) return 'moderate'
  return 'low'
}
