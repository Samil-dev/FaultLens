import { create } from 'zustand'
import type {
  System,
  Experiment,
  ExperimentRunData,
  ScenarioComparison,
} from '../types/api'
import { fetchExperimentHistory } from '../services/api'
import { setStoredSystemId } from '../utils/activeSystem'
import { buildHealthyNodeStates, computeSettledNodeStates, type NodeVisualState } from '../utils/nodeStates'

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

// Gate on the initial app shell: 'loading' while the app is figuring out
// which system was active before a reload, 'ready' once resolved (or once
// it's given up and fallen back to whatever system is already in memory).
export type BootstrapStatus = 'loading' | 'ready'

interface ExperimentStore {
  // ── System ──────────────────────────────────────────────────────────────────
  system: System
  setSystem: (system: System) => void

  // All systems persisted in the backend (as of the last time it was fetched
  // — by bootstrap or by opening the System Switcher). Used to populate the
  // switcher; not authoritative between fetches.
  systems: System[]
  setSystems: (systems: System[]) => void

  // Makes `system` the single source of truth for "which system is active" —
  // used by bootstrap restoration, system import, and system switching alike,
  // so all three go through exactly one code path and can never leave the
  // app in a mixed state (e.g. Digital Twin on system A, History on system B).
  // Persists the choice to localStorage and loads that system's real,
  // backend-sourced experiment history.
  activateSystem: (system: System) => Promise<void>

  // Resolves once on startup: was there a previously-active system to
  // restore? Gates the initial render so the UI never flashes the demo
  // system before swapping to the real restored one.
  bootstrapStatus: BootstrapStatus
  setBootstrapStatus: (status: BootstrapStatus) => void

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
  setNodeStatesBulk: (states: Record<string, NodeVisualState>) => void
  resetNodeStates: () => void

  // ── Results ──────────────────────────────────────────────────────────────────
  lastResult: ExperimentRunData | null
  setLastResult: (result: ExperimentRunData | null) => void
  experimentHistory: ExperimentRunData[]
  pushHistory: (result: ExperimentRunData) => void
  setExperimentHistory: (history: ExperimentRunData[]) => void

  // ── Scenario comparison ───────────────────────────────────────────────────────
  comparisonResult: ScenarioComparison | null
  setComparisonResult: (result: ScenarioComparison | null) => void

  // ── Active sidebar panel ──────────────────────────────────────────────────────
  activeSidebarPanel: string
  setActiveSidebarPanel: (panel: string) => void

  // ── System import modal ──────────────────────────────────────────────────────
  systemImportOpen: boolean
  setSystemImportOpen: (open: boolean) => void

  // ── System switcher modal ────────────────────────────────────────────────────
  systemSwitcherOpen: boolean
  setSystemSwitcherOpen: (open: boolean) => void

  // Jumps straight to a past experiment result — used by History. Restores
  // not just the result panel but the *whole* workflow context: which node
  // it targeted (selection follows it) and how the Digital Twin looked once
  // that run settled (node states follow it too), so reviewing history looks
  // like looking at a freshly-completed run instead of a stale graph.
  viewResult: (result: ExperimentRunData) => void
}

export const useStore = create<ExperimentStore>((set, get) => ({
  // ── System ───────────────────────────────────────────────────────────────────
  system: DEMO_SYSTEM,
  setSystem: (system) =>
    set({ system, nodeStates: buildHealthyNodeStates(system) }),

  systems: [],
  setSystems: (systems) => set({ systems }),

  activateSystem: async (system) => {
    // Switch immediately and clear everything that belonged to the previous
    // system, so nothing from it can remain visible while history loads.
    // Also lands back on the Digital Twin tab — the natural first view of
    // any (newly activated) system, per the core-workflow requirement that
    // import/switch always leads back to the twin rather than wherever the
    // sidebar happened to be pointed at.
    set({
      system,
      nodeStates: buildHealthyNodeStates(system),
      selectedNodeId: null,
      lastResult: null,
      comparisonResult: null,
      pendingExperiment: null,
      phase: 'idle',
      experimentHistory: [],
      activeSidebarPanel: 'system',
    })
    setStoredSystemId(system.id)

    try {
      const history = await fetchExperimentHistory(system.id)
      // Guard against a stale response landing after the user switched
      // systems again while this fetch was in flight.
      if (get().system.id === system.id) {
        set({ experimentHistory: history })
      }
    } catch {
      // History stays empty; the header's connection indicator already
      // communicates a backend outage — no need to duplicate that here.
    }
  },

  bootstrapStatus: 'loading',
  setBootstrapStatus: (bootstrapStatus) => set({ bootstrapStatus }),

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
  nodeStates: buildHealthyNodeStates(DEMO_SYSTEM),
  setNodeState: (id, partial) =>
    set((s) => ({
      nodeStates: {
        ...s.nodeStates,
        [id]: { ...s.nodeStates[id], ...partial },
      },
    })),
  setNodeStatesBulk: (nodeStates) => set({ nodeStates }),
  resetNodeStates: () =>
    set((s) => ({ nodeStates: buildHealthyNodeStates(s.system) })),

  // ── Results ───────────────────────────────────────────────────────────────────
  lastResult: null,
  setLastResult: (lastResult) => set({ lastResult }),
  experimentHistory: [],
  pushHistory: (result) =>
    set((s) => ({ experimentHistory: [result, ...s.experimentHistory].slice(0, 20) })),
  setExperimentHistory: (experimentHistory) => set({ experimentHistory }),

  // ── Comparison ────────────────────────────────────────────────────────────────
  comparisonResult: null,
  setComparisonResult: (comparisonResult) => set({ comparisonResult }),

  // ── Sidebar ───────────────────────────────────────────────────────────────────
  activeSidebarPanel: 'system',
  setActiveSidebarPanel: (activeSidebarPanel) => set({ activeSidebarPanel }),

  // ── System import modal ──────────────────────────────────────────────────────
  systemImportOpen: false,
  setSystemImportOpen: (systemImportOpen) => set({ systemImportOpen }),

  // ── System switcher modal ────────────────────────────────────────────────────
  systemSwitcherOpen: false,
  setSystemSwitcherOpen: (systemSwitcherOpen) => set({ systemSwitcherOpen }),

  viewResult: (result) =>
    set((s) => ({
      lastResult: result,
      phase: 'done',
      selectedNodeId: result.run.target_node,
      nodeStates: computeSettledNodeStates(s.system, result),
      pendingExperiment: null,
    })),
}))
