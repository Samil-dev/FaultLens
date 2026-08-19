import { useMemo, useState } from 'react'
import { useStore } from '../../store/experimentStore'
import { StatusBadge } from '../ui/StatusBadge'
import { ComparisonPanel } from '../panels/ComparisonPanel'
import { MetricsPanel } from '../panels/MetricsPanel'
import { AIInsightStatusNotice } from '../panels/AIInsightStatusNotice'
import type { NodeStatus } from '../../types/api'
import { EXPERIMENT_TYPE_LABEL, formatRelativeTime, formatTimestamp } from '../../utils/format'
import { estimateCriticality, getDirectDependencies, getDirectDependents, getPotentialAffectedNodes } from '../../utils/graph'
import { EXPERIMENT_TYPES } from '../../constants/experimentTypes'

const CRITICALITY_COLOR: Record<string, string> = {
  low: 'var(--risk-low)',
  moderate: 'var(--risk-moderate)',
  high: 'var(--risk-high)',
}

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
    viewResult,
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

  const nodeName = (id: string) => system.nodes.find((n) => n.id === id)?.name ?? id

  const directDependencies = selectedNode ? getDirectDependencies(system, selectedNode.id) : []
  const directDependents = selectedNode ? getDirectDependents(system, selectedNode.id) : []
  const potentialAffected = selectedNode ? getPotentialAffectedNodes(system, selectedNode.id) : []
  const criticality = selectedNode ? estimateCriticality(potentialAffected.length, system.nodes.length) : 'low'

  const degradedCount = system.nodes.filter(
    (n) => (nodeStates[n.id]?.status ?? (n.status as NodeStatus)) === 'degraded',
  ).length
  const criticalCount = lastResult ? lastResult.analysis.impact.critical_nodes.length : null
  const lastExperimentAt = experimentHistory[0]?.run.created_at
    ? formatRelativeTime(experimentHistory[0].run.created_at)
    : null

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
                <span className="stat-label">Degraded</span>
                <span className="stat-value" style={{ color: degradedCount > 0 ? 'var(--color-degraded)' : undefined }}>
                  {degradedCount}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Critical</span>
                <span className={criticalCount === null ? 'stat-value value-na' : 'stat-value'} style={{ color: criticalCount ? 'var(--color-failed)' : undefined }}>
                  {criticalCount === null ? 'N/A' : criticalCount}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Status</span>
                <StatusBadge variant={systemStatus} />
              </div>
              {lastResult && (
                <div className="stat-row">
                  <span className="stat-label">Resilience</span>
                  <span className="stat-value">{lastResult.resilience_score.score.toFixed(0)}</span>
                </div>
              )}
              {lastResult && (
                <div className="stat-row">
                  <span className="stat-label">Risk</span>
                  <StatusBadge variant={lastResult.analysis.risk.level} dot />
                </div>
              )}
              <div className="stat-row">
                <span className="stat-label">Last experiment</span>
                <span className={lastExperimentAt ? 'stat-value' : 'stat-value value-na'} style={{ fontSize: 11 }}>
                  {lastExperimentAt ?? 'None yet'}
                </span>
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

                  <div style={{ marginTop: 8 }}>
                    <span className="label" style={{ display: 'block', marginBottom: 3 }}>
                      Dependencies ({directDependencies.length})
                    </span>
                    <p className="value-na" style={{ fontSize: 11, margin: 0 }}>
                      {directDependencies.length > 0
                        ? directDependencies.map(nodeName).join(', ')
                        : 'None — this is a leaf dependency.'}
                    </p>
                  </div>

                  <div style={{ marginTop: 8 }}>
                    <span className="label" style={{ display: 'block', marginBottom: 3 }}>
                      Dependents ({directDependents.length})
                    </span>
                    <p className={directDependents.length > 0 ? '' : 'value-na'} style={{ fontSize: 11, margin: 0 }}>
                      {directDependents.length > 0
                        ? directDependents.map(nodeName).join(', ')
                        : 'None — nothing depends on this service.'}
                    </p>
                  </div>

                  {selectedNode.description && (
                    <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
                      {selectedNode.description}
                    </p>
                  )}

                  {/* ── Impact Preview — topology-based, computed before running anything ── */}
                  <div style={{
                    marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--border)',
                  }}>
                    <p className="panel-section-title" style={{ marginBottom: 6 }}>Impact Preview</p>
                    <div className="stat-row">
                      <span className="stat-label">Potential blast radius</span>
                      <span className="stat-value">
                        {potentialAffected.length} / {system.nodes.length} nodes
                      </span>
                    </div>
                    <div className="progress-bar" style={{ margin: '4px 0 8px' }}>
                      <div
                        className="progress-fill"
                        style={{
                          width: `${system.nodes.length > 0 ? (potentialAffected.length / system.nodes.length) * 100 : 0}%`,
                          background: 'var(--risk-moderate)',
                        }}
                      />
                    </div>
                    <div className="stat-row">
                      <span className="stat-label">Criticality</span>
                      <span
                        className="stat-value"
                        style={{ color: CRITICALITY_COLOR[criticality], textTransform: 'uppercase', fontSize: 11 }}
                      >
                        {criticality}
                      </span>
                    </div>
                    <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.5 }}>
                      Estimated from the dependency graph — how many services would potentially be
                      affected if this node failed. Not a measured result; run an experiment for that.
                    </p>
                  </div>

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

        {/* ── Experiment panel — templates for every backend-supported scenario ── */}
        {activeSidebarPanel === 'experiment' && (
          <div className="panel-section">
            <p className="panel-section-title">Chaos Scenarios</p>
            {EXPERIMENT_TYPES.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => {
                  if (!selectedNodeId) return
                  setPendingExperiment({
                    system_id: system.id,
                    target_node: selectedNodeId,
                    type: s.value,
                    duration_seconds: 30,
                  })
                  setPhase('configuring')
                }}
                disabled={!selectedNodeId}
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px',
                  marginBottom: 8,
                  cursor: selectedNodeId ? 'pointer' : 'not-allowed',
                  opacity: selectedNodeId ? 1 : 0.7,
                  color: 'inherit',
                  font: 'inherit',
                }}
              >
                <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 4 }}>
                  <span>{s.icon}</span>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>{s.label}</span>
                </div>
                <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.simulates}</p>
                <p style={{
                  fontSize: 10, color: 'var(--text-muted)',
                  marginTop: 4, fontStyle: 'italic',
                  borderTop: '1px solid var(--border)', paddingTop: 4,
                }}>
                  {selectedNodeId
                    ? `Click to configure this scenario for "${nodeName(selectedNodeId)}"`
                    : 'Select a node on the graph first'}
                </p>
              </button>
            ))}
          </div>
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

        {/* ── AI panel — observed data / AI interpretation / recommendation narrative ── */}
        {activeSidebarPanel === 'ai' && (
          lastResult ? (
            <>
              <div className="panel-section">
                <p className="panel-section-title" style={{ color: 'var(--color-healthy)' }}>Observed Data</p>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                  <strong style={{ color: 'var(--text-primary)' }}>
                    {lastResult.analysis.impact.affected_nodes}
                  </strong>{' '}
                  of <strong style={{ color: 'var(--text-primary)' }}>{lastResult.analysis.impact.total_nodes}</strong>{' '}
                  nodes were affected ({(lastResult.analysis.impact.blast_radius * 100).toFixed(0)}% blast radius).
                  Average recovery took{' '}
                  <strong style={{ color: 'var(--text-primary)' }}>
                    {lastResult.analysis.recovery.average_recovery_seconds.toFixed(1)}s
                  </strong>
                  {lastResult.analysis.recovery.failed_recoveries.length > 0
                    ? `, with ${lastResult.analysis.recovery.failed_recoveries.length} node(s) failing to recover.`
                    : ', and every affected node recovered.'}
                </p>
              </div>

              <div className="panel-section">
                <p className="panel-section-title" style={{ color: 'var(--accent)' }}>AI Interpretation</p>
                {lastResult.ai_analysis.status === 'available' && lastResult.ai_analysis.analysis ? (
                  <>
                    <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 8 }}>
                      {lastResult.ai_analysis.analysis.root_cause}
                    </p>
                    <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                      {lastResult.ai_analysis.analysis.risk_interpretation}
                    </p>
                  </>
                ) : (
                  <AIInsightStatusNotice insight={lastResult.ai_analysis} />
                )}
              </div>

              <div className="panel-section">
                <p className="panel-section-title" style={{ color: 'var(--risk-moderate)' }}>Recommendation</p>
                {lastResult.analysis.recommendations.slice(0, 2).map((rec, i) => (
                  <div key={i} className="rec-card">
                    <span className="rec-card-title">{rec.title}</span>
                    <p className="rec-card-desc">{rec.description}</p>
                  </div>
                ))}
              </div>

              {lastResult.ai_analysis.status === 'available' && lastResult.ai_analysis.analysis && (
                <div className="panel-section">
                  <p className="panel-section-title">Confidence</p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div className="progress-bar" style={{ flex: 1 }}>
                      <div
                        className="progress-fill"
                        style={{ width: `${lastResult.ai_analysis.analysis.confidence * 100}%`, background: 'var(--accent)' }}
                      />
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                      {(lastResult.ai_analysis.analysis.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="stat-row" style={{ marginTop: 6 }}>
                    <span className="stat-label">Provider</span>
                    <span className="stat-value" style={{ textTransform: 'uppercase', fontSize: 10 }}>
                      {lastResult.ai_analysis.provider}
                    </span>
                  </div>
                </div>
              )}
            </>
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
              {experimentHistory.length >= 2 && (() => {
                const seq = [...experimentHistory].slice(0, 6).reverse()
                const delta = seq[seq.length - 1].resilience_score.score - seq[0].resilience_score.score
                return (
                  <div className="panel-section">
                    <p className="panel-section-title">Resilience Trend</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                      {seq.map((r, i) => (
                        <span key={r.run.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          {i > 0 && <span style={{ color: 'var(--text-muted)' }}>→</span>}
                          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
                            {r.resilience_score.score.toFixed(0)}
                          </span>
                        </span>
                      ))}
                    </div>
                    <p style={{ fontSize: 11, marginTop: 6, color: delta >= 0 ? 'var(--color-healthy)' : 'var(--color-failed)' }}>
                      {delta >= 0 ? '+' : ''}{delta.toFixed(0)} over the last {seq.length} runs
                    </p>
                  </div>
                )
              })()}
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
                      onClick={() => viewResult(result)}
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
