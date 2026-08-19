import { useEffect, useState } from 'react'
import { useStore } from '../../store/experimentStore'
import { fetchSystems } from '../../services/api'
import type { System } from '../../types/api'

type LoadState = 'loading' | 'ready' | 'error'

export function SystemSwitcherModal() {
  const {
    systemSwitcherOpen, setSystemSwitcherOpen,
    system: activeSystem, activateSystem, setSystems,
    setSystemImportOpen,
  } = useStore()

  const [systems, setLocalSystems] = useState<System[]>([])
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [error, setError] = useState<string | null>(null)
  const [switchingTo, setSwitchingTo] = useState<string | null>(null)
  const [switchError, setSwitchError] = useState<string | null>(null)

  useEffect(() => {
    if (!systemSwitcherOpen) return
    let cancelled = false
    setLoadState('loading')
    setError(null)
    setSwitchError(null)
    fetchSystems()
      .then((result) => {
        if (cancelled) return
        setLocalSystems(result)
        setSystems(result) // keep the store's cached copy fresh too
        setLoadState('ready')
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Could not reach the backend.')
        setLoadState('error')
      })
    return () => { cancelled = true }
  }, [systemSwitcherOpen, setSystems])

  if (!systemSwitcherOpen) return null

  function close() {
    setSystemSwitcherOpen(false)
  }

  async function handleSwitch(target: System) {
    if (target.id === activeSystem.id) {
      close()
      return
    }
    setSwitchingTo(target.id)
    setSwitchError(null)
    try {
      await activateSystem(target)
      close()
    } catch (err) {
      // Keep the modal open so the user can see what happened and retry,
      // instead of silently doing nothing while still on the old system.
      setSwitchError(err instanceof Error ? err.message : `Could not switch to "${target.name}".`)
    } finally {
      setSwitchingTo(null)
    }
  }

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && close()}>
      <div
        className="modal-box"
        role="dialog"
        aria-modal="true"
        aria-labelledby="system-switcher-title"
        style={{ width: 460 }}
      >
        <div className="modal-title" id="system-switcher-title">
          ⇄ Switch System
        </div>

        {loadState === 'loading' && (
          <div className="empty-state" style={{ padding: '28px 0' }}>
            <span className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
            <span style={{ marginTop: 8 }}>Loading persisted systems…</span>
          </div>
        )}

        {loadState === 'error' && (
          <div style={{
            background: 'rgba(248,81,73,0.1)', border: '1px solid rgba(248,81,73,0.25)',
            borderRadius: 'var(--radius-md)', padding: '10px 12px', marginBottom: 16,
          }}>
            <p style={{ fontSize: 11, color: 'var(--color-failed)', marginBottom: 8 }}>
              Unavailable — {error}
            </p>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => {
                setLoadState('loading')
                fetchSystems()
                  .then((result) => { setLocalSystems(result); setSystems(result); setLoadState('ready') })
                  .catch((err) => { setError(err instanceof Error ? err.message : 'Could not reach the backend.'); setLoadState('error') })
              }}
            >
              Retry
            </button>
          </div>
        )}

        {switchError && (
          <div style={{
            background: 'rgba(248,81,73,0.1)', border: '1px solid rgba(248,81,73,0.25)',
            borderRadius: 'var(--radius-md)', padding: '10px 12px', marginBottom: 12,
          }}>
            <p style={{ fontSize: 11, color: 'var(--color-failed)' }}>
              Switch failed — {switchError}
            </p>
          </div>
        )}

        {loadState === 'ready' && (
          <div style={{ marginBottom: 16, maxHeight: '50vh', overflowY: 'auto' }}>
            {systems.length === 0 ? (
              <div className="empty-state" style={{ padding: '20px 0' }}>
                <span className="empty-icon">⬡</span>
                <span>No systems found on the backend.</span>
              </div>
            ) : (
              systems.map((sys) => {
                const isActive = sys.id === activeSystem.id
                const isSwitching = switchingTo === sys.id
                return (
                  <button
                    key={sys.id}
                    type="button"
                    onClick={() => handleSwitch(sys)}
                    disabled={switchingTo !== null}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10, width: '100%', textAlign: 'left',
                      background: isActive ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                      border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border)'}`,
                      borderRadius: 'var(--radius-md)', padding: '10px 12px', marginBottom: 6,
                      cursor: switchingTo !== null ? 'default' : 'pointer', color: 'inherit', font: 'inherit',
                    }}
                  >
                    <span
                      aria-hidden="true"
                      style={{
                        width: 9, height: 9, borderRadius: '50%', flexShrink: 0,
                        background: isActive ? 'var(--accent)' : 'transparent',
                        border: `1.5px solid ${isActive ? 'var(--accent)' : 'var(--border-bright)'}`,
                      }}
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {sys.name}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                        {sys.nodes.length} node{sys.nodes.length === 1 ? '' : 's'} · {sys.dependencies.length} dependenc{sys.dependencies.length === 1 ? 'y' : 'ies'}
                      </div>
                    </div>
                    {isActive && <span className="label" style={{ color: 'var(--accent)' }}>Active</span>}
                    {isSwitching && <span className="spinner" style={{ width: 12, height: 12, borderWidth: 1.5 }} />}
                  </button>
                )
              })
            )}
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between' }}>
          <button
            className="btn btn-ghost"
            onClick={() => { close(); setSystemImportOpen(true) }}
          >
            ⬡ Import New System
          </button>
          <button className="btn btn-ghost" onClick={close}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
