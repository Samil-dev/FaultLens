import { useStore } from '../../store/experimentStore'
import { StatusBadge } from '../ui/StatusBadge'
import { ScoreRing } from '../ui/ScoreRing'
import { NextExperimentSuggestion } from '../panels/NextExperimentSuggestion'
import { AIInsightStatusNotice } from '../panels/AIInsightStatusNotice'
import type { Recommendation } from '../../types/api'
import { EXPERIMENT_TYPE_LABEL } from '../../utils/format'

const PRIORITY_COLOR: Record<string, string> = {
  high:   'var(--risk-high)',
  medium: 'var(--risk-moderate)',
  low:    'var(--risk-low)',
}

export function RightPanel() {
  const { lastResult, phase, system } = useStore()

  if (phase === 'idle' || phase === 'selecting' || phase === 'configuring') {
    return (
      <aside className="app-right-panel">
        <div style={{ padding: '14px 14px 10px', borderBottom: '1px solid var(--border)' }}>
          <p className="panel-section-title" style={{ marginBottom: 0 }}>Resilience Panel</p>
        </div>
        <div className="empty-state" style={{ padding: '40px 20px' }}>
          <span className="empty-icon">🛡</span>
          <span style={{ maxWidth: 200, lineHeight: 1.6 }}>
            Run a chaos experiment to see the resilience analysis, AI insights, and metric comparisons here.
          </span>
        </div>
        <div className="panel-section" style={{ marginTop: 'auto' }}>
          <p className="panel-section-title">About FaultLens</p>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.7 }}>
            Don't wait for a production failure.<br />
            Simulate it, understand it, and improve resilience before it happens.
          </p>
        </div>
      </aside>
    )
  }

  if (phase === 'running') {
    return (
      <aside className="app-right-panel">
        <div style={{ padding: '14px 14px 10px', borderBottom: '1px solid var(--border)' }}>
          <p className="panel-section-title" style={{ marginBottom: 0 }}>Resilience Panel</p>
        </div>
        <div className="empty-state" style={{ padding: '40px 20px' }}>
          <span className="spinner" style={{ width: 24, height: 24, borderWidth: 2 }} />
          <span style={{ marginTop: 8, color: 'var(--accent)' }}>Simulating experiment…</span>
        </div>
      </aside>
    )
  }

  if (!lastResult) return null

  const { resilience_score, analysis, ai_analysis, comparisons, events, run } = lastResult

  const targetNode = system.nodes.find((n) => n.id === run.target_node)
  const targetFailed = run.type === 'service_down'

  return (
    <aside className="app-right-panel">
      {/* ── Header ── */}
      <div style={{
        padding: '12px 14px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <p className="panel-section-title" style={{ marginBottom: 0 }}>Resilience Panel</p>
        <StatusBadge variant={analysis.risk.level} />
      </div>

      <div className="scroll-area">

        {/* ── Score ── */}
        <div className="panel-section" style={{ textAlign: 'center' }}>
          <p className="panel-section-title">Resilience Score</p>
          <div style={{ display: 'flex', justifyContent: 'center', position: 'relative', marginBottom: 8 }}>
            <ScoreRing score={resilience_score.score} size={90} strokeWidth={7} />
          </div>
          <StatusBadge variant={resilience_score.rating as any} label={resilience_score.rating} />
          <div className="stat-row" style={{ marginTop: 10 }}>
            <span className="stat-label">Affected nodes</span>
            <span className="stat-value" style={{ color: resilience_score.affected_nodes > 0 ? 'var(--color-failed)' : 'var(--color-healthy)' }}>
              {resilience_score.affected_nodes} / {resilience_score.total_nodes}
            </span>
          </div>
        </div>

        {/* ── Experiment target ── */}
        <div className="panel-section">
          <p className="panel-section-title">Experiment Target</p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, fontWeight: 600 }}>{targetNode?.name ?? run.target_node}</span>
            <StatusBadge variant={targetFailed ? 'failed' : 'degraded'} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
            <p style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              {targetNode?.node_type ?? 'unknown type'}
            </p>
            <p style={{ fontSize: 10, color: 'var(--text-muted)' }}>
              {EXPERIMENT_TYPE_LABEL[run.type] ?? run.type}
            </p>
          </div>
        </div>

        {/* ── Failure propagation path ── */}
        {run.affected_nodes.length > 0 && (
          <div className="panel-section">
            <p className="panel-section-title">Failure Propagation Path</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {[run.target_node, ...run.affected_nodes].map((nodeId, i) => {
                const isOrigin = i === 0
                const node = system.nodes.find((n) => n.id === nodeId)
                const recovery = run.recoveries.find((r) => r.node_id === nodeId)
                const recovered = recovery?.recovery_status === 'recovered'
                const stepColor = isOrigin
                  ? (targetFailed ? 'var(--color-failed)' : 'var(--color-degraded)')
                  : 'var(--color-degraded)'
                return (
                  <div key={nodeId} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 16 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: stepColor, flexShrink: 0, marginTop: 4 }} />
                      {i < run.affected_nodes.length && (
                        <span style={{ width: 1, flex: 1, minHeight: 18, background: 'var(--border)' }} />
                      )}
                    </div>
                    <div style={{ paddingBottom: 10 }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)' }}>
                        {i + 1}. {node?.name ?? nodeId}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                        {isOrigin ? 'Origin' : 'Affected'}
                        {recovery && (
                          <span style={{ color: recovered ? 'var(--color-healthy)' : 'var(--color-failed)' }}>
                            {' · '}{recovered ? `recovered in ${recovery.recovery_time_seconds?.toFixed(1)}s` : 'did not recover'}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* ── Impact ── */}
        <div className="panel-section">
          <p className="panel-section-title">
            Impact Analysis
            <span style={{ marginLeft: 6, color: 'var(--color-healthy)' }}>· Observed</span>
          </p>

          <div className="stat-row">
            <span className="stat-label">Blast radius</span>
            <span className="stat-value">
              {analysis.impact.affected_nodes} / {analysis.impact.total_nodes} nodes
              {' · '}
              {(analysis.impact.blast_radius * 100).toFixed(0)}%
            </span>
          </div>

          {/* Blast radius bar */}
          <div className="progress-bar" style={{ margin: '4px 0 8px' }}>
            <div
              className="progress-fill"
              style={{
                width: `${analysis.impact.blast_radius * 100}%`,
                background: analysis.impact.blast_radius >= 0.5
                  ? 'var(--risk-critical)'
                  : analysis.impact.blast_radius >= 0.25
                  ? 'var(--risk-high)'
                  : 'var(--color-degraded)',
              }}
            />
          </div>

          <div className="stat-row">
            <span className="stat-label">Metric impact</span>
            <span className="stat-value">
              {(analysis.impact.average_metric_impact * 100).toFixed(0)}%
            </span>
          </div>

          {analysis.impact.critical_nodes.length > 0 && (
            <div style={{ marginTop: 6 }}>
              <span className="label" style={{ display: 'block', marginBottom: 4 }}>Critical nodes</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {analysis.impact.critical_nodes.map((id) => {
                  const n = system.nodes.find((x) => x.id === id)
                  return (
                    <span key={id} style={{
                      fontSize: 10, padding: '2px 6px',
                      background: 'rgba(248,81,73,0.1)',
                      color: 'var(--color-failed)',
                      borderRadius: 4,
                      border: '1px solid rgba(248,81,73,0.2)',
                    }}>
                      {n?.name ?? id}
                    </span>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* ── Recovery ── */}
        <div className="panel-section">
          <p className="panel-section-title">
            Recovery
            <span style={{ marginLeft: 6, color: 'var(--color-healthy)' }}>· Observed</span>
          </p>
          <div className="stat-row">
            <span className="stat-label">Recovered</span>
            <span className="stat-value" style={{ color: 'var(--color-healthy)' }}>
              {analysis.recovery.recovered_nodes} / {analysis.recovery.total_recovery_nodes}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Avg time</span>
            <span className="stat-value">{analysis.recovery.average_recovery_seconds.toFixed(1)}s</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Max time</span>
            <span className="stat-value">{analysis.recovery.max_recovery_seconds.toFixed(1)}s</span>
          </div>
          {analysis.recovery.failed_recoveries.length > 0 && (
            <div style={{ marginTop: 6 }}>
              <span className="label" style={{ color: 'var(--risk-critical)' }}>
                Failed recoveries
              </span>
              {analysis.recovery.failed_recoveries.map((id) => (
                <div key={id} style={{ fontSize: 11, color: 'var(--color-failed)', padding: '2px 0' }}>
                  {system.nodes.find((n) => n.id === id)?.name ?? id}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Risk ── */}
        <div className="panel-section">
          <p className="panel-section-title">
            Risk Assessment
            <span style={{ marginLeft: 6, color: 'var(--color-healthy)' }}>· Observed</span>
          </p>
          <StatusBadge variant={analysis.risk.level} label={`${analysis.risk.level} risk`} />
          <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 6, lineHeight: 1.6 }}>
            {analysis.risk.reason}
          </p>
        </div>

        {/* ── AI Analysis ── */}
        <div className="panel-section">
          <p className="panel-section-title" style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span>🤖</span> AI Analysis
            <span style={{ color: 'var(--accent)' }}>· AI interpretation</span>
            <span style={{
              marginLeft: 'auto', fontSize: 9, padding: '1px 5px',
              background: 'var(--bg-elevated)', borderRadius: 3,
              color: 'var(--text-muted)', textTransform: 'uppercase' as const,
              letterSpacing: '0.06em',
            }}>
              {ai_analysis.provider}
            </span>
          </p>

          {ai_analysis.status !== 'available' || !ai_analysis.analysis ? (
            <AIInsightStatusNotice insight={ai_analysis} />
          ) : (
            <>
              <div style={{
                background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)', padding: '10px 12px', marginBottom: 10,
              }}>
                <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                  {ai_analysis.analysis.summary}
                </p>
              </div>
              <div style={{ marginBottom: 8 }}>
                <span className="label" style={{ display: 'block', marginBottom: 4 }}>Root cause</span>
                <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {ai_analysis.analysis.root_cause}
                </p>
              </div>
              <div style={{ marginBottom: 8 }}>
                <span className="label" style={{ display: 'block', marginBottom: 4 }}>Risk interpretation</span>
                <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {ai_analysis.analysis.risk_interpretation}
                </p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
                <span className="label">Confidence</span>
                <div className="progress-bar" style={{ flex: 1 }}>
                  <div
                    className="progress-fill"
                    style={{
                      width: `${ai_analysis.analysis.confidence * 100}%`,
                      background: 'var(--accent)',
                    }}
                  />
                </div>
                <span style={{ fontSize: 10, color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>
                  {(ai_analysis.analysis.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </>
          )}
        </div>

        {/* ── Recommendations ── */}
        <div className="panel-section">
          <p className="panel-section-title">
            Recommendations
            <span style={{ marginLeft: 6, color: 'var(--risk-moderate)' }}>· Recommendation</span>
          </p>
          {analysis.recommendations.map((rec: Recommendation, i: number) => (
            <div key={i} className="rec-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span className="rec-card-title">{rec.title}</span>
                <span style={{
                  fontSize: 9, fontWeight: 700, letterSpacing: '0.06em',
                  textTransform: 'uppercase' as const, color: PRIORITY_COLOR[rec.priority] ?? 'var(--text-muted)',
                }}>
                  {rec.priority}
                </span>
              </div>
              <p className="rec-card-desc">{rec.description}</p>
            </div>
          ))}
        </div>

        {/* ── Metric comparisons ── */}
        {comparisons.length > 0 && (
          <div className="panel-section">
            <p className="panel-section-title">Metric Comparisons</p>
            <div className="table-scroll">
            <table className="metric-table">
              <thead>
                <tr>
                  <th>Node</th>
                  <th>CPU Δ</th>
                  <th>Mem Δ</th>
                  <th>Latency Δ</th>
                  <th>Err Δ</th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((c) => {
                  const node = system.nodes.find((n) => n.id === c.node_id)
                  return (
                    <tr key={c.node_id}>
                      <td className="metric-table-name" style={{ color: 'var(--text-primary)' }} title={node?.name ?? c.node_id}>{node?.name ?? c.node_id}</td>
                      <td className={c.cpu_usage_delta !== 0 ? 'delta-positive' : 'delta-zero'}>
                        {c.cpu_usage_delta > 0 ? '+' : ''}{c.cpu_usage_delta.toFixed(1)}
                      </td>
                      <td className={c.memory_usage_delta !== 0 ? 'delta-positive' : 'delta-zero'}>
                        {c.memory_usage_delta > 0 ? '+' : ''}{c.memory_usage_delta.toFixed(1)}
                      </td>
                      <td className={c.latency_delta_ms !== 0 ? 'delta-positive' : 'delta-zero'}>
                        {c.latency_delta_ms > 0 ? '+' : ''}{c.latency_delta_ms.toFixed(0)}ms
                      </td>
                      <td className={c.error_rate_delta !== 0 ? 'delta-positive' : 'delta-zero'}>
                        {c.error_rate_delta > 0 ? '+' : ''}{c.error_rate_delta.toFixed(1)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            </div>
          </div>
        )}

        {/* ── Experiment timeline ── */}
        <div className="panel-section">
          <p className="panel-section-title">Experiment Timeline</p>
          <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: -6, marginBottom: 8 }}>
            Failure injection order, then recovery order (by measured recovery time).
          </p>
          <div className="event-log">
            {events.map((evt) => {
              const color = evt.event_type === 'failure_injected'
                ? 'var(--color-failed)'
                : evt.event_type === 'node_degraded'
                ? 'var(--color-degraded)'
                : evt.event_type === 'node_recovered'
                ? 'var(--color-healthy)'
                : 'var(--color-recovering)'

              const label = evt.event_type.replace(/_/g, ' ')
              const node = system.nodes.find((n) => n.id === evt.node_id)

              return (
                <div key={evt.id} className="event-item">
                  <span className="event-type-dot" style={{ background: color }} />
                  <div>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                      {node?.name ?? evt.node_id}
                    </span>
                    <span style={{ color: 'var(--text-muted)', marginLeft: 4 }}>{label}</span>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      severity {(evt.severity * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              )
            })}
            {[...run.recoveries]
              .sort((a, b) => (a.recovery_time_seconds ?? Infinity) - (b.recovery_time_seconds ?? Infinity))
              .map((rec) => {
                const node = system.nodes.find((n) => n.id === rec.node_id)
                const recovered = rec.recovery_status === 'recovered'
                return (
                  <div key={`recovery-${rec.node_id}`} className="event-item">
                    <span className="event-type-dot" style={{ background: recovered ? 'var(--color-healthy)' : 'var(--color-failed)' }} />
                    <div>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                        {node?.name ?? rec.node_id}
                      </span>
                      <span style={{ color: 'var(--text-muted)', marginLeft: 4 }}>
                        {recovered ? 'recovered' : 'failed to recover'}
                      </span>
                      {rec.recovery_time_seconds !== null && (
                        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                          T+{rec.recovery_time_seconds.toFixed(1)}s
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
          </div>
        </div>

        {/* ── Recommended next experiment ── */}
        <NextExperimentSuggestion analysis={analysis} lastTargetNode={run.target_node} />
      </div>
    </aside>
  )
}
