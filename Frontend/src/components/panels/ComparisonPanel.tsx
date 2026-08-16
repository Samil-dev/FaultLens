import { useState } from 'react'
import { useStore } from '../../store/experimentStore'
import { compareExperiments } from '../../services/api'
import { StatusBadge } from '../ui/StatusBadge'
import { EXPERIMENT_TYPE_LABEL } from '../../utils/format'

export function ComparisonPanel() {
  const { experimentHistory, comparisonResult, setComparisonResult, system } = useStore()
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function toggleSelect(runId: string) {
    setSelectedIds((prev) =>
      prev.includes(runId)
        ? prev.filter((id) => id !== runId)
        : prev.length < 4
        ? [...prev, runId]
        : prev
    )
  }

  async function handleCompare() {
    if (selectedIds.length < 2) return
    setLoading(true)
    setError(null)
    try {
      const result = await compareExperiments({ run_ids: selectedIds })
      setComparisonResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed')
    } finally {
      setLoading(false)
    }
  }

  function handleClear() {
    setComparisonResult(null)
    setSelectedIds([])
    setError(null)
  }

  if (experimentHistory.length === 0) {
    return (
      <div className="empty-state">
        <span className="empty-icon">⇄</span>
        <span>Run at least two experiments to compare scenarios.</span>
      </div>
    )
  }

  return (
    <>
      {/* ── Run selector ── */}
      {!comparisonResult && (
        <div className="panel-section">
          <p className="panel-section-title">Select Runs to Compare</p>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>
            Choose 2–4 experiment runs, then press Compare.
          </p>

          {experimentHistory.map((run) => {
            const selected = selectedIds.includes(run.run.id)
            const targetName = system.nodes.find((n) => n.id === run.run.target_node)?.name ?? run.run.target_node
            return (
              <div
                key={run.run.id}
                onClick={() => toggleSelect(run.run.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    toggleSelect(run.run.id)
                  }
                }}
                role="checkbox"
                aria-checked={selected}
                tabIndex={0}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 8px',
                  marginBottom: 4,
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
                  background: selected ? 'rgba(59,130,212,0.07)' : 'var(--bg-elevated)',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                <span aria-hidden="true" style={{
                  width: 14, height: 14, borderRadius: 3,
                  border: `2px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
                  background: selected ? 'var(--accent)' : 'transparent',
                  flexShrink: 0,
                }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {targetName} · {EXPERIMENT_TYPE_LABEL[run.run.type] ?? run.run.type}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                    Score {run.resilience_score.score} · {run.analysis.risk.level} risk
                  </div>
                </div>
                <StatusBadge variant={run.resilience_score.rating as any} dot={false} />
              </div>
            )
          })}

          {error && (
            <p style={{ fontSize: 11, color: 'var(--color-failed)', marginTop: 6 }}>{error}</p>
          )}

          <button
            className="btn btn-primary"
            style={{ marginTop: 10, width: '100%', justifyContent: 'center' }}
            disabled={selectedIds.length < 2 || loading}
            onClick={handleCompare}
          >
            {loading
              ? (<><span className="spinner" style={{ width: 11, height: 11, borderWidth: 1.5 }} /> Comparing…</>)
              : `⇄ Compare ${selectedIds.length} Run${selectedIds.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      )}

      {/* ── Comparison table ── */}
      {comparisonResult && (() => {
        const runs = comparisonResult.runs
        // "Best" per metric, computed only from the runs actually being compared —
        // used purely to highlight, never to alter the underlying values.
        const bestScore = Math.max(...runs.map((r) => r.resilience_score.score))
        const bestBlastRadius = Math.min(...runs.map((r) => r.analysis.impact.blast_radius))
        const bestRecovery = Math.min(...runs.map((r) => r.analysis.recovery.average_recovery_seconds))

        return (
        <div className="panel-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <p className="panel-section-title" style={{ marginBottom: 0 }}>Comparison</p>
            <button
              className="btn btn-ghost"
              style={{ fontSize: 10, padding: '2px 8px' }}
              onClick={handleClear}
            >
              ✕ Clear
            </button>
          </div>
          {runs.length > 1 && (
            <p style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 10 }}>
              "✓ best" marks the safest score, smallest blast radius, and fastest recovery among the compared runs.
            </p>
          )}

          {runs.map((run, idx) => (
            <div key={run.run.id} style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              padding: '10px',
              marginBottom: 8,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)' }}>
                  Run {idx + 1}
                </span>
                <StatusBadge variant={run.analysis.risk.level} />
              </div>
              <p style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 6 }}>
                {EXPERIMENT_TYPE_LABEL[run.run.type] ?? run.run.type} on {run.run.target_node}
              </p>
              <div className="stat-row">
                <span className="stat-label">Score</span>
                <span
                  className={`stat-value ${run.resilience_score.score === bestScore ? 'stat-winner' : ''}`}
                  style={{ fontVariantNumeric: 'tabular-nums' }}
                >
                  {run.resilience_score.score}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Blast radius</span>
                <span className={`stat-value ${run.analysis.impact.blast_radius === bestBlastRadius ? 'stat-winner' : ''}`}>
                  {(run.analysis.impact.blast_radius * 100).toFixed(0)}%
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Affected</span>
                <span className="stat-value">
                  {run.analysis.impact.affected_nodes} / {run.analysis.impact.total_nodes}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Avg recovery</span>
                <span className={`stat-value ${run.analysis.recovery.average_recovery_seconds === bestRecovery ? 'stat-winner' : ''}`}>
                  {run.analysis.recovery.average_recovery_seconds.toFixed(1)}s
                </span>
              </div>
              <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.5, fontStyle: 'italic' }}>
                {run.ai_analysis.summary.slice(0, 120)}…
              </p>
            </div>
          ))}
        </div>
        )
      })()}
    </>
  )
}
