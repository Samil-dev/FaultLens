import { useEffect } from 'react'
import { useStore } from '../../store/experimentStore'
import { fetchHealth } from '../../services/api'
import { EXPERIMENT_TYPE_LABEL } from '../../utils/format'
import { IBMBobMcpStatus } from './IBMBobMcpStatus'

export function Header() {
  const {
    connectionStatus, setConnectionStatus, phase, system, lastResult, selectedNodeId,
    setSystemImportOpen, setSystemSwitcherOpen,
  } = useStore()

  // Breadcrumb reflecting where the user is in the experiment lifecycle:
  // System -> selected node -> scenario -> lifecycle stage.
  const selectedNode = selectedNodeId ? system.nodes.find((n) => n.id === selectedNodeId) : null
  const experimentInFlight = phase === 'running' || phase === 'propagating'
  const breadcrumb: string[] = [system.name]
  if (selectedNode) breadcrumb.push(selectedNode.name)
  if (phase === 'configuring') breadcrumb.push('Configure experiment')
  if (phase === 'running' || phase === 'propagating') breadcrumb.push('Simulating')
  if (phase === 'done' && lastResult) {
    breadcrumb.push(EXPERIMENT_TYPE_LABEL[lastResult.run.type] ?? lastResult.run.type)
    breadcrumb.push('Analysis')
  }

  // Poll backend health
  useEffect(() => {
    let mounted = true

    async function check() {
      try {
        await fetchHealth()
        if (mounted) setConnectionStatus('online')
      } catch {
        if (mounted) setConnectionStatus('offline')
      }
    }

    check()
    const id = setInterval(check, 10_000)
    return () => {
      mounted = false
      clearInterval(id)
    }
  }, [setConnectionStatus])

  const score = lastResult?.resilience_score.score
  const risk  = lastResult?.analysis.risk.level

  return (
    <header className="app-header">
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginRight: 8 }}>
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
          <polygon points="11,2 20,7 20,15 11,20 2,15 2,7" stroke="var(--accent)" strokeWidth="1.5" fill="none" />
          <polygon points="11,5 17,8.5 17,13.5 11,17 5,13.5 5,8.5" stroke="var(--accent)" strokeWidth="0.7" fill="var(--accent-dim)" />
          <circle cx="11" cy="11" r="2.5" fill="var(--accent)" />
        </svg>
        <span style={{ fontWeight: 700, fontSize: 14, letterSpacing: '0.04em', color: 'var(--text-primary)' }}>
          FAULT<span style={{ color: 'var(--accent)' }}>LENS</span>
        </span>
        <span style={{
          fontSize: 9, fontWeight: 700, letterSpacing: '0.12em',
          color: 'var(--text-muted)', borderLeft: '1px solid var(--border)',
          paddingLeft: 8, textTransform: 'uppercase'
        }}>
          Chaos Engineering &amp; Resilience Intelligence
        </span>
      </div>

      {/* Breadcrumb: system -> selected node -> lifecycle stage */}
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 6, marginRight: 'auto', minWidth: 0, overflow: 'hidden' }}
        aria-label="Experiment lifecycle breadcrumb"
      >
        {breadcrumb.map((part, i) =>
          i === 0 ? (
            <button
              key={i}
              type="button"
              onClick={() => setSystemSwitcherOpen(true)}
              disabled={experimentInFlight}
              title={experimentInFlight ? 'Wait for the running experiment to finish before switching systems' : 'Switch active system'}
              aria-label={`Active system: ${part}. Click to switch systems.`}
              style={{
                display: 'flex', alignItems: 'center', gap: 4,
                background: 'transparent', border: 'none',
                cursor: experimentInFlight ? 'not-allowed' : 'pointer', padding: '2px 4px',
                marginLeft: -4, borderRadius: 'var(--radius-sm)',
                fontSize: 12,
                opacity: experimentInFlight ? 0.5 : 1,
                color: breadcrumb.length === 1 ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: breadcrumb.length === 1 ? 600 : 400,
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 220,
              }}
            >
              {part}
              <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>▾</span>
            </button>
          ) : (
            <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
              <span style={{ color: 'var(--text-muted)' }}>/</span>
              <span style={{
                fontSize: 12,
                color: i === breadcrumb.length - 1 ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: i === breadcrumb.length - 1 ? 600 : 400,
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              }}>
                {part}
              </span>
            </span>
          )
        )}
        <button
          className="btn btn-ghost btn-sm"
          style={{ marginLeft: 10, flexShrink: 0 }}
          onClick={() => setSystemImportOpen(true)}
          disabled={experimentInFlight}
          aria-label="Import a system architecture"
          title={experimentInFlight ? 'Wait for the running experiment to finish before importing a system' : 'Import a system architecture'}
        >
          ⬡ Import System
        </button>
      </div>

      {/* Resilience score pill */}
      {score !== undefined && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-bright)',
          borderRadius: 20, padding: '3px 10px'
        }}>
          <span className="label">Resilience</span>
          <span style={{
            fontWeight: 700, fontSize: 13,
            color: score >= 60 ? 'var(--rating-good)' : score >= 40 ? 'var(--rating-moderate)' : 'var(--risk-critical)',
            fontVariantNumeric: 'tabular-nums',
          }}>
            {score.toFixed(1)}
          </span>
        </div>
      )}

      {/* Risk badge */}
      {risk && (
        <div style={{
          padding: '2px 8px',
          borderRadius: 4,
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: '0.08em',
          textTransform: 'uppercase' as const,
          background: `var(--badge-${risk}-bg, var(--bg-elevated))`,
          color: `var(--risk-${risk})`,
          border: `1px solid var(--risk-${risk})`,
          opacity: 0.9,
        }}>
          {risk} risk
        </div>
      )}

      {/* Phase status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {phase === 'running' && (
          <>
            <span className="spinner" style={{ width: 12, height: 12, borderWidth: 1.5 }} />
            <span style={{ fontSize: 11, color: 'var(--accent)' }}>Running experiment…</span>
          </>
        )}
        {phase === 'propagating' && (
          <span style={{ fontSize: 11, color: 'var(--color-failed)', animation: 'blink 0.8s ease infinite' }}>
            ⚠ Propagating failure
          </span>
        )}
        {phase === 'done' && (
          <span style={{ fontSize: 11, color: 'var(--color-healthy)' }}>✓ Simulation complete</span>
        )}
      </div>

      {/* Connection status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 8 }}>
        <span className={`conn-dot conn-${connectionStatus}`} />
        <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'capitalize' }}>
          {connectionStatus}
        </span>
      </div>

      {/* IBM Bob — real, observable MCP integration status (never a fabricated "Connected") */}
      <IBMBobMcpStatus />
    </header>
  )
}
