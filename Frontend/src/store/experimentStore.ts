import { create } from 'zustand'
import type {
  System,
  Experiment,
  ExperimentRunData,
  NodeStatus,
} from '../types/api'

// Demo system that ships with the app — a realistic microservices architecture
export const DEMO_SYSTEM: System = {
  id: 'sys-demo',
  name: 'E-Commerce Platform',
  nodes: [
    { id: 'gateway', name: 'API Gateway', node_type: 'gateway', status: 'healthy' },
    { id: 'auth', name: 'Auth Service', node_type: 'service', status: 'healthy' },
    { id: 'catalog', name: 'Catalog Service', node_type: 'service', status: 'healthy' },
    { id: 'cart', name: 'Cart Service', node_type: 'service', status: 'healthy' },
    { id: 'orders', name: 'Order Service', node_type: 'service', status: 'healthy' },
    { id: 'payments', name: 'Payment Service', node_type: 'service', status: 'healthy' },
    { id: 'notifications', name: 'Notification Service', node_type: 'service', status: 'healthy' },
    { id: 'db-main', name: 'Primary Database', node_type: 'database', status: 'healthy' },
    { id: 'db-cache', name: 'Redis Cache', node_type: 'cache', status: 'healthy' },
    { id: 'queue', name: 'Message Queue', node_type: 'queue', status: 'healthy' },
  ],
  dependencies: [
    { source: 'gateway', target: 'auth', type: 'depends_on' },
    { source: 'gateway', target: 'catalog', type: 'depends_on' },
    { source: 'gateway', target: 'cart', type: 'depends_on' },
    { source: 'gateway', target: 'orders', type: 'depends_on' },
    { source: 'cart', target: 'db-cache', type: 'depends_on' },
    { source: 'catalog', target: 'db-main', type: 'depends_on' },
    { source: 'orders', target: 'db-main', type: 'depends_on' },
    { source: 'orders', target: 'payments', type: 'depends_on' },
    { source: 'orders', target: 'queue', type: 'depends_on' },
    { source: 'notifications', target: 'queue', type: 'depends_on' },
    { source: 'auth', target: 'db-main', type: 'depends_on' },
  ],
}

export type AppPhase =
  | 'idle'
  | 'selecting'    // user clicked a node
  | 'configuring'  // experiment modal open
  | 'running'      // waiting for API response
  | 'propagating'  // animating failure through graph
  | 'done'         // results visible

export type ConnectionStatus = 'connecting' | 'online' | 'offline'

interface NodeVisualState {
  status: NodeStatus
  highlighted: boolean
  animating: boolean
}

interface ExperimentStore {
  // ── System ──────────────────────────────────────────────────────────────────
  system: System
  setSystem: (system: System) => void

  // ── Connection ───────────────────────────────────────────────────────────────
  connectionStatus: ConnectionStatus
  setConnectionStatus: (s: ConnectionStatus) => void

  // ── Selection ───────────────────────────────────────────────────────────────
  selectedNodeId: string | null
  selectNode: (id: string | null) => void

  // ── Phase ────────────────────────────────────────────────────────────────────
  phase: AppPhase
  setPhase: (phase: AppPhase) => void

  // ── Active experiment config ─────────────────────────────────────────────────
  pendingExperiment: Partial<Experiment> | null
  setPendingExperiment: (exp: Partial<Experiment> | null) => void

  // ── Node visual states (driven by events/results) ─────────────────────────────
  nodeStates: Record<string, NodeVisualState>
  setNodeState: (id: string, state: Partial<NodeVisualState>) => void
  resetNodeStates: () => void

  // ── Results ──────────────────────────────────────────────────────────────────
  lastResult: ExperimentRunData | null
  setLastResult: (result: ExperimentRunData | null) => void
  experimentHistory: ExperimentRunData[]
  pushHistory: (result: ExperimentRunData) => void

  // ── Active sidebar panel ──────────────────────────────────────────────────────
  activeSidebarPanel: string
  setActiveSidebarPanel: (panel: string) => void
}

function buildDefaultNodeStates(system: System): Record<string, NodeVisualState> {
  const states: Record<string, NodeVisualState> = {}
  for (const node of system.nodes) {
    states[node.id] = { status: node.status as NodeStatus, highlighted: false, animating: false }
  }
  return states
}

export const useStore = create<ExperimentStore>((set) => ({
  // ── System ───────────────────────────────────────────────────────────────────
  system: DEMO_SYSTEM,
  setSystem: (system) =>
    set({ system, nodeStates: buildDefaultNodeStates(system) }),

  // ── Connection ────────────────────────────────────────────────────────────────
  connectionStatus: 'connecting',
  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),

  // ── Selection ────────────────────────────────────────────────────────────────
  selectedNodeId: null,
  selectNode: (id) => set({ selectedNodeId: id }),

  // ── Phase ─────────────────────────────────────────────────────────────────────
  phase: 'idle',
  setPhase: (phase) => set({ phase }),

  // ── Pending experiment config ─────────────────────────────────────────────────
  pendingExperiment: null,
  setPendingExperiment: (pendingExperiment) => set({ pendingExperiment }),

  // ── Node visual states ────────────────────────────────────────────────────────
  nodeStates: buildDefaultNodeStates(DEMO_SYSTEM),
  setNodeState: (id, partial) =>
    set((s) => ({
      nodeStates: {
        ...s.nodeStates,
        [id]: { ...s.nodeStates[id], ...partial },
      },
    })),
  resetNodeStates: () =>
    set((s) => ({ nodeStates: buildDefaultNodeStates(s.system) })),

  // ── Results ───────────────────────────────────────────────────────────────────
  lastResult: null,
  setLastResult: (lastResult) => set({ lastResult }),
  experimentHistory: [],
  pushHistory: (result) =>
    set((s) => ({ experimentHistory: [result, ...s.experimentHistory].slice(0, 20) })),

  // ── Sidebar ───────────────────────────────────────────────────────────────────
  activeSidebarPanel: 'system',
  setActiveSidebarPanel: (activeSidebarPanel) => set({ activeSidebarPanel }),
}))
