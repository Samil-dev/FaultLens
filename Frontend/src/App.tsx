import { useEffect } from 'react'
import { Header } from './components/layout/Header'
import { LeftSidebar } from './components/layout/LeftSidebar'
import { RightPanel } from './components/layout/RightPanel'
import { GraphCanvas } from './components/experiment/GraphCanvas'
import { ExperimentModal } from './components/experiment/ExperimentModal'
import { ImportSystemModal } from './components/system/ImportSystemModal'
import { SystemSwitcherModal } from './components/system/SystemSwitcherModal'
import { fetchSystems } from './services/api'
import { useStore } from './store/experimentStore'
import { clearStoredSystemId, getStoredSystemId } from './utils/activeSystem'

export default function App() {
  const {
    activateSystem, setSystems, bootstrapStatus, setBootstrapStatus,
    noSystemsAvailable, setNoSystemsAvailable, setSystemImportOpen,
  } = useStore()

  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      const storedId = getStoredSystemId()

      try {
        const systems = await fetchSystems()
        if (cancelled) return
        setSystems(systems)

        // A previously-active system takes priority over the demo system —
        // but only if it still actually exists in the backend.
        let target = storedId ? systems.find((s) => s.id === storedId) : undefined
        if (storedId && !target) {
          // The stored id is stale (system was deleted, DB was reset, etc.).
          clearStoredSystemId()
        }

        // Fall back to the seeded demo system, or whatever the backend
        // happens to have, if there's nothing (valid) to restore.
        if (!target) {
          target = systems.find((s) => s.id === 'sys-demo') ?? systems[0]
        }

        if (target) {
          await activateSystem(target)
        } else {
          // The backend answered but genuinely has zero persisted systems.
          // The in-memory DEMO_SYSTEM constant the store still holds must
          // never be presented as "the active system" in this case — it
          // was never activated, never persisted, and reloading would lose
          // it silently. Show a real empty state instead.
          setNoSystemsAvailable(true)
        }
      } catch {
        // Backend unreachable at boot. Keep whatever system is already in
        // memory (the bundled DEMO_SYSTEM) so the dashboard stays usable;
        // the header's connection indicator honestly reports the outage.
      } finally {
        if (!cancelled) setBootstrapStatus('ready')
      }
    }

    void bootstrap()
    return () => {
      cancelled = true
    }
    // Intentionally runs once: this is startup restoration, not a
    // reactive sync — subsequent system changes go through activateSystem.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (bootstrapStatus === 'loading') {
    return (
      <div style={{
        height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 14, background: 'var(--bg-base)',
      }}>
        <svg width="32" height="32" viewBox="0 0 22 22" fill="none">
          <polygon points="11,2 20,7 20,15 11,20 2,15 2,7" stroke="var(--accent)" strokeWidth="1.5" fill="none" />
          <polygon points="11,5 17,8.5 17,13.5 11,17 5,13.5 5,8.5" stroke="var(--accent)" strokeWidth="0.7" fill="var(--accent-dim)" />
          <circle cx="11" cy="11" r="2.5" fill="var(--accent)" />
        </svg>
        <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
        <span style={{ fontSize: 12, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
          Restoring workspace…
        </span>
      </div>
    )
  }

  if (noSystemsAvailable) {
    return (
      <div style={{
        height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 14, background: 'var(--bg-base)',
      }}>
        <span style={{ fontSize: 40, opacity: 0.5 }}>⬡</span>
        <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
          No systems yet
        </span>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: 320, textAlign: 'center', lineHeight: 1.6 }}>
          The backend has no persisted architectures. Import a system to create its Digital Twin and start a resilience workflow.
        </span>
        <button className="btn btn-primary" onClick={() => setSystemImportOpen(true)}>
          ⬡ Import System
        </button>
        <ImportSystemModal />
      </div>
    )
  }

  return (
    <div className="app-shell">
      <Header />
      <LeftSidebar />
      <GraphCanvas />
      <RightPanel />
      <ExperimentModal />
      <ImportSystemModal />
      <SystemSwitcherModal />
    </div>
  )
}
