import { DependencyGraph } from '../graph/DependencyGraph'
import { useStore } from '../../store/experimentStore'

export function GraphCanvas() {
  const { selectedNodeId, system, phase, setPhase, setPendingExperiment } = useStore()
  const selectedNode = selectedNodeId ? system.nodes.find((n) => n.id === selectedNodeId) : null

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
    <div className="app-canvas" style={{ position: 'relative' }}>
      {/* Graph fills the canvas */}
      <DependencyGraph />

      {/* Selected node floating action */}
      {selectedNode && phase !== 'running' && phase !== 'propagating' && (
        <div style={{
          position: 'absolute',
          bottom: 20,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-bright)',
          borderRadius: 'var(--radius-lg)',
          padding: '10px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          animation: 'slideUp 0.14s ease',
          pointerEvents: 'all',
        }}>
          <div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 1 }}>Selected</div>
            <div style={{ fontSize: 13, fontWeight: 700 }}>{selectedNode.name}</div>
          </div>
          <button
            className="btn btn-danger"
            onClick={handleRunExperiment}
          >
            ⚡ Run Experiment
          </button>
        </div>
      )}

      {/* Phase banner — done state */}
      {phase === 'done' && (
        <div style={{
          position: 'absolute',
          top: 12,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(8,12,16,0.85)',
          border: '1px solid var(--border-bright)',
          borderRadius: 'var(--radius-md)',
          padding: '6px 14px',
          fontSize: 11,
          color: 'var(--text-secondary)',
          backdropFilter: 'blur(4px)',
          pointerEvents: 'none',
        }}>
          Experiment complete — see the Resilience Panel →
        </div>
      )}

      {/* Graph legend */}
      <div style={{
        position: 'absolute',
        top: 12,
        right: 12,
        background: 'var(--bg-panel)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '8px 10px',
        display: 'flex',
        flexDirection: 'column',
        gap: 5,
      }}>
        {[
          { color: 'var(--color-healthy)',    label: 'Healthy'    },
          { color: 'var(--color-degraded)',   label: 'Degraded'   },
          { color: 'var(--color-failed)',     label: 'Failed'     },
          { color: 'var(--color-recovering)', label: 'Recovering' },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
