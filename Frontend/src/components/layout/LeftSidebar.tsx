import { useMemo, useState } from 'react'
import { useStore } from '../../store/experimentStore'
import { StatusBadge } from '../ui/StatusBadge'
import { ComparisonPanel } from '../panels/ComparisonPanel'
import { MetricsPanel } from '../panels/MetricsPanel'
import type { NodeStatus } from '../../types/api'
import { EXPERIMENT_TYPE_LABEL, formatTimestamp } from '../../utils/format'

const NAV_ITEMS = [
  { id: 'system',     icon: '⬡', label: 'Digital Twin'       },
  { id: 'experiment', icon: '⚡', label: 'Chaos Experiments'  },
  { id: 'analysis',   icon: '📊', label: 'Resilience Analysis'},
  { id: 'ai',         icon: '🤖', label: 'AI Insights'        },
  { id: 'compare',    icon: '⇄',  label: 'Compare Scenarios'  },
  { id: 'metrics',    icon: '📈', label: 'Metrics'            },
  { id: 'history',    icon: '🕑', label: 'History'            },
]

// Worst-of ranking used to roll many node states up into one system status.
const STATUS_SEVERITY: Record<NodeStatus, number> = {
  failed: 3,
  degraded: 2,
  recovering: 1,
  healthy: 0,
}

export function LeftSidebar() {
  const {
    activeSidebarPanel,
    setActiveSidebarPanel,
    system,
    selectedNodeId,
    nodeStates,
    phase,
    setPhase,
    experimentHistory,
    lastResult,
    selectNode,
    setPendingExperiment,
    setLastResult,
  } = useStore()

  const [historyFilter, setHistoryFilter] = useState('')

  const selectedNode = selectedNodeId
    ? system.nodes.find((n) => n.id === selectedNodeId)
    : null
  const selectedState = selectedNodeId ? nodeStates[selectedNodeId] : null

  // Rolls every node's live status up into one system-wide indicator —
  // worst status wins (failed > degraded > recovering > healthy).
  const systemStatus: NodeStatus = useMemo(() => {
    let worst: NodeStatus = 'healthy'
    for (const node of system.nodes) {
      const s = nodeStates[node.id]?.status ?? (node.status as NodeStatus)
      if (STATUS_SEVERITY[s] > STATUS_SEVERITY[worst]) worst = s
    }
    return worst
  }, [system.nodes, nodeStates])

  const dependsOnCount = selectedNode
    ? system.dependencies.filter((d) => d.source === selectedNode.id).length
    : 0
  const dependedByCount = selectedNode
    ? system.dependencies.filter((d) => d.target === selectedNode.id).length
    : 0

  const filteredHistory = useMemo(() => {
    const q = historyFilter.trim().toLowerCase()
    if (!q) return experimentHistory
    return experimentHistory.filter((result) => {
      const targetName = system.nodes.find((n) => n.id === result.run.target_node)?.name ?? result.run.target_node
      return (
        targetName.toLowerCase().includes(q) ||
        result.run.type.toLowerCase().includes(q) ||
        result.analysis.risk.level.toLowerCase().includes(q)
      )
    })
  }, [experimentHistory, historyFilter, system.nodes])

  function handleRunExperiment() {
    if (!selectedNodeId) return
    setPendingExperiment({
      system_id: system.id,
      target_node: selectedNodeId,
      type: 'service_down',
      duration_seconds: 30,
    })
    setPhase('configuring')
  }

  return (
    <aside className="app-sidebar">
      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <div
            key={item.id}
            className={`sidebar-nav-item ${activeSidebarPanel === item.id ? 'active' : ''}`}
            onClick={() => setActiveSidebarPanel(item.id)}
          >
            <span style={{ fontSize: 13 }}>{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}
      </nav>

      {/* Panel content */}
      <div className="scroll-area" style={{ padding: '0 0 16px' }}>

        {/* ── System panel ──────────────────────────────────────────────── */}
        {activeSidebarPanel === 'system' && (
          <>
            <div className="panel-section">
              <p className="panel-section-title">System Overview</p>
              <div className="stat-row">
                <span className="stat-label">Total nodes</span>
                <span className="stat-value">{system.nodes.length}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Dependencies</span>
                <span className="stat-value">{system.dependencies.length}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Status</span>
                <StatusBadge variant={systemStatus} />
              </div>
            </div>

            <div className="panel-section">
              <p className="panel-section-title">Nodes</p>
              {system.nodes.map((node) => {
                const vs = nodeStates[node.id]
                return (
                  <div
                    key={node.id}
                    onClick={() => selectNode(selectedNodeId === node.id ? null : node.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '5px 0',
                      cursor: 'pointer',
                      borderBottom: '1px solid var(--border)',
                    }}
                  >
                    <span style={{
                      fontSize: 12,
                      color: selectedNodeId === node.id ? 'var(--accent)' : 'var(--text-secondary)',
                      fontWeight: selectedNodeId === node.id ? 600 : 400,
                    }}>
                      {node.name}
                    </span>
                    <StatusBadge variant={vs?.status ?? node.status} dot={true} label="" />
                  </div>
                )
              })}
            </div>

            {/* Selected node detail */}
            {selectedNode && selectedState && (
              <div className="panel-section">
                <p className="panel-section-title">Selected Node</p>
                <div className="node-detail-card">
                  <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
                    {selectedNode.name}
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Type</span>
                    <span className="stat-value" style={{ textTransform: 'uppercase', fontSize: 10 }}>
                      {selectedNode.node_type}
                    </span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Status</span>
                    <StatusBadge variant={selectedState.status} />
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Depends on</span>
                    <span className="stat-value">{dependsOnCount} service{dependsOnCount === 1 ? '' : 's'}</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Depended on by</span>
                    <span className="stat-value">{dependedByCount} service{dependedByCount === 1 ? '' : 's'}</span>
                  </div>
                  {selectedNode.description && (
                    <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                      {selectedNode.description}
                    </p>
                  )}
                  <button
                    className="btn btn-danger btn-sm"
                    style={{ marginTop: 10, width: '100%', justifyContent: 'center' }}
                    onClick={handleRunExperiment}
                    disabled={phase === 'running' || phase === 'propagating'}
                  >
                    ⚡ Run Experiment
                  </button>
                </div>
              </div>
            )}

            {!selectedNode && (
              <div className="empty-state" style={{ padding: '24px 14px' }}>
                <span className="empty-icon">◈</span>
                <span>Click a node on the graph to select it and run an experiment.</span>
              </div>
            )}
          </>
        )}

        {/* ── Experiment panel ──────────────────────────────────────────── */}
        {activeSidebarPanel === 'experiment' && (
          <>
            <div className="panel-section">
              <p className="panel-section-title">Chaos Scenarios</p>
              {[
                { type: 'service_down',        label: 'Service Down',        desc: 'Bring a node completely offline',          icon: '🔴', active: true },
                { type: 'latency_spike',        label: 'Latency Spike',       desc: 'Inject high latency into a node',          icon: '⏱', active: true },
                { type: 'resource_exhaustion',  label: 'Resource Exhaustion', desc: 'Saturate CPU and memory resources',        icon: '📉', active: true },
                { type: 'traffic_spike',        label: 'Traffic Spike',       desc: 'Simulate a sudden request-volume overload', icon: '📶', active: true },
              ].map((s) => (
                <div key={s.type} style={{
                  background: 'var(--bg-elevated)',
                  border: `1px solid ${s.active ? 'var(--border)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '10px',
                  marginBottom: 8,
                  opacity: s.active ? 1 : 0.5,
                }}>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 4 }}>
                    <span>{s.icon}</span>
                    <span style={{ fontSize: 12, fontWeight: 600 }}>{s.label}</span>
                    {!s.active && (
                      <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 'auto', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                        soon
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.desc}</p>
                  {s.active && (
                    <p style={{
                      fontSize: 10, color: 'var(--text-muted)',
                      marginTop: 4, fontStyle: 'italic',
                      borderTop: '1px solid var(--border)', paddingTop: 4,
                    }}>
                      Select a node on the graph, then click "Run Experiment"
                    </p>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {/* ── Analysis panel ───────────────────────────────────────────── */}
        {activeSidebarPanel === 'analysis' && (
          lastResult ? (
            <div className="panel-section">
              <p className="panel-section-title">
                Last Analysis
                <span style={{ marginLeft: 6, color: 'var(--color-healthy)' }}>· Observed data</span>
              </p>
              <div className="stat-row">
                <span className="stat-label">Blast radius</span>
                <span className="stat-value">
                  {(lastResult.analysis.impact.blast_radius * 100).toFixed(0)}%
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Affected nodes</span>
                <span className="stat-value" style={{ color: 'var(--color-failed)' }}>
                  {lastResult.analysis.impact.affected_nodes} / {lastResult.analysis.impact.total_nodes}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Risk level</span>
                <StatusBadge variant={lastResult.analysis.risk.level} dot />
              </div>
              <div className="stat-row">
                <span className="stat-label">Avg recovery</span>
                <span className="stat-value">
                  {lastResult.analysis.recovery.average_recovery_seconds.toFixed(1)}s
                </span>
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 8, lineHeight: 1.6 }}>
                {lastResult.analysis.risk.reason}
              </p>
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon">📊</span>
              <span>Run an experiment to see resilience analysis here.</span>
            </div>
          )
        )}

        {/* ── AI panel ─────────────────────────────────────────────────── */}
        {activeSidebarPanel === 'ai' && (
          lastResult ? (
            <div className="panel-section">
              <p className="panel-section-title">
                AI Insights
                <span style={{ marginLeft: 6, color: 'var(--accent)' }}>· AI interpretation</span>
              </p>
              <div style={{
                background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)', padding: 10, marginBottom: 8,
              }}>
                <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {lastResult.ai_analysis.summary}
                </p>
              </div>
              <div className="stat-row">
                <span className="stat-label">Provider</span>
                <span className="stat-value" style={{ textTransform: 'uppercase', fontSize: 10 }}>
                  {lastResult.ai_analysis.provider}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Confidence</span>
                <span className="stat-value">
                  {(lastResult.ai_analysis.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon">🤖</span>
              <span>AI insights appear after running an experiment.</span>
            </div>
          )
        )}

        {/* ── History panel ─────────────────────────────────────────────── */}
        {activeSidebarPanel === 'history' && (
          experimentHistory.length > 0 ? (
            <div>
              <div style={{ padding: '10px 14px 4px' }}>
                <input
                  type="search"
                  className="form-input"
                  placeholder="Filter by node, scenario, or risk…"
                  aria-label="Filter experiment history"
                  value={historyFilter}
                  onChange={(e) => setHistoryFilter(e.target.value)}
                />
              </div>
              {filteredHistory.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-icon">🔍</span>
                  <span>No runs match "{historyFilter}".</span>
                </div>
              ) : (
                filteredHistory.map((result) => {
                  const targetName = system.nodes.find((n) => n.id === result.run.target_node)?.name
                    ?? result.run.target_node
                  return (
                    <button
                      key={result.run.id}
                      type="button"
                      className="history-item"
                      onClick={() => {
                        setLastResult(result)
                        setPhase('done')
                      }}
                      style={{ width: '100%', textAlign: 'left', cursor: 'pointer' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 2 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                          {targetName}
                        </span>
                        <StatusBadge variant={result.resilience_score.rating as any} dot={false} />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                          {EXPERIMENT_TYPE_LABEL[result.run.type] ?? result.run.type}
                        </span>
                        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                          {formatTimestamp(result.run.created_at)}
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                          Score: {result.resilience_score.score}
                        </span>
                        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                          {result.analysis.risk.level} risk
                        </span>
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon">🕑</span>
              <span>No experiments run yet.</span>
            </div>
          )
        )}

        {/* ── Compare panel ─────────────────────────────────────────────── */}
        {activeSidebarPanel === 'compare' && <ComparisonPanel />}

        {/* ── Metrics panel ────────────────────────────────────────────── */}
        {activeSidebarPanel === 'metrics' && <MetricsPanel />}
      </div>
    </aside>
  )
}
