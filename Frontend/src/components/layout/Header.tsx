import { useEffect } from 'react'
import { useStore } from '../../store/experimentStore'
import { fetchHealth } from '../../services/api'

export function Header() {
  const { connectionStatus, setConnectionStatus, phase, system, lastResult } = useStore()

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
          CODE<span style={{ color: 'var(--accent)' }}>TWIN</span>
        </span>
        <span style={{
          fontSize: 9, fontWeight: 700, letterSpacing: '0.12em',
          color: 'var(--text-muted)', borderLeft: '1px solid var(--border)',
          paddingLeft: 8, textTransform: 'uppercase'
        }}>
          ChaosLab
        </span>
      </div>

      {/* System name */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginRight: 'auto' }}>
        <span className="label">System</span>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{system.name}</span>
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
          <span style={{ fontSize: 11, color: 'var(--color-healthy)' }}>✓ Experiment complete</span>
        )}
      </div>

      {/* Connection status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 8 }}>
        <span className={`conn-dot conn-${connectionStatus}`} />
        <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'capitalize' }}>
          {connectionStatus}
        </span>
      </div>
    </header>
  )
}
