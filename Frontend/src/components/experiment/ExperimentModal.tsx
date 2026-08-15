import { useState } from 'react'
import { useStore } from '../../store/experimentStore'
import { runExperiment } from '../../services/api'
import type { ExperimentType } from '../../types/api'

const EXPERIMENT_TYPES: { value: ExperimentType; label: string; supported: boolean; desc: string }[] = [
  { value: 'service_down',        label: 'Service Down',        supported: true,  desc: 'Take a node completely offline' },
  { value: 'latency_spike',       label: 'Latency Spike',       supported: true,  desc: 'Inject high latency into a node' },
  { value: 'resource_exhaustion', label: 'Resource Exhaustion', supported: true,  desc: 'Saturate CPU and memory resources' },
  { value: 'traffic_spike',       label: 'Traffic Spike',       supported: false, desc: 'Coming soon' },
]

export function ExperimentModal() {
  const {
    pendingExperiment,
    setPendingExperiment,
    system,
    phase,
    setPhase,
    setLastResult,
    pushHistory,
    setNodeState,
    resetNodeStates,
  } = useStore()

  const [expType, setExpType] = useState<ExperimentType>('service_down')
  const [duration, setDuration] = useState(30)
  const [error, setError] = useState<string | null>(null)

  if (phase !== 'configuring' || !pendingExperiment) return null

  const targetNodeId = pendingExperiment.target_node!
  const targetNode = system.nodes.find((n) => n.id === targetNodeId)

  function close() {
    setPendingExperiment(null)
    setPhase('idle')
    setError(null)
  }

  async function handleRun() {
    if (!pendingExperiment?.target_node) return
    setError(null)
    setPhase('running')

    const experimentId = `exp-${Date.now()}`

    const request = {
      system,
      experiment: {
        id: experimentId,
        system_id: system.id,
        target_node: pendingExperiment.target_node,
        type: expType,
        duration_seconds: duration,
      },
    }

    try {
      const response = await runExperiment(request)

      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? 'Experiment failed')
      }

      const data = response.data

      // ── Animate failure propagation ─────────────────────────────────────
      setPhase('propagating')
      resetNodeStates()

      // Mark target node with appropriate status based on experiment type
      const targetFinalStatus = expType === 'service_down' ? 'failed' : 'degraded'
      setNodeState(pendingExperiment.target_node, { status: targetFinalStatus, animating: true, highlighted: true })

      // Stagger degradation of affected nodes
      const affectedNodes = data.run.affected_nodes
      for (let i = 0; i < affectedNodes.length; i++) {
        await delay(300 + i * 250)
        setNodeState(affectedNodes[i], { status: 'degraded', animating: true, highlighted: true })
      }

      await delay(600)

      // Transition to recovering
      for (const recovery of data.run.recoveries) {
        if (recovery.recovery_status === 'recovered') {
          setNodeState(recovery.node_id, { status: 'recovering', animating: true })
        } else {
          setNodeState(recovery.node_id, { status: 'failed', animating: false })
        }
      }

      await delay(800)

      // Final state — recovered nodes become healthy (except permanently failed)
      for (const recovery of data.run.recoveries) {
        if (recovery.recovery_status === 'recovered') {
          setNodeState(recovery.node_id, { status: 'healthy', animating: false, highlighted: false })
        }
      }

      // Target node stays at its final status
      setNodeState(pendingExperiment.target_node, { status: targetFinalStatus, animating: false, highlighted: true })

      // Store results
      setLastResult(data)
      pushHistory(data)
      setPhase('done')
      setPendingExperiment(null)

    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      setError(msg)
      setPhase('configuring')
      resetNodeStates()
    }
  }

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && close()}>
      <div className="modal-box">
        <div className="modal-title">
          ⚡ Run Chaos Experiment
        </div>

        {/* Target node info */}
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-bright)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 12px',
          marginBottom: 16,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>TARGET NODE</div>
            <div style={{ fontSize: 13, fontWeight: 700 }}>{targetNode?.name ?? targetNodeId}</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: 2 }}>
              {targetNode?.node_type}
            </div>
          </div>
          <div style={{
            fontSize: 20, opacity: 0.4,
          }}>🎯</div>
        </div>

        {/* Experiment type */}
        <div className="form-group">
          <label className="form-label">Failure Scenario</label>
          <select
            className="form-select"
            value={expType}
            onChange={(e) => setExpType(e.target.value as ExperimentType)}
          >
            {EXPERIMENT_TYPES.map((t) => (
              <option key={t.value} value={t.value} disabled={!t.supported}>
                {t.label}{!t.supported ? ' (coming soon)' : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Duration */}
        <div className="form-group">
          <label className="form-label">Duration (seconds)</label>
          <input
            className="form-input"
            type="number"
            min={1}
            max={300}
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
          />
        </div>

        {/* Warning */}
        <div style={{
          background: 'rgba(210,153,34,0.08)',
          border: '1px solid rgba(210,153,34,0.2)',
          borderRadius: 'var(--radius-md)',
          padding: '8px 12px',
          marginBottom: 16,
          fontSize: 11,
          color: 'var(--color-degraded)',
          lineHeight: 1.5,
        }}>
          ⚠ This is a simulated experiment. No real infrastructure will be affected.
        </div>

        {/* Error */}
        {error && (
          <div style={{
            background: 'rgba(248,81,73,0.1)',
            border: '1px solid rgba(248,81,73,0.25)',
            borderRadius: 'var(--radius-md)',
            padding: '8px 12px',
            marginBottom: 16,
            fontSize: 11,
            color: 'var(--color-failed)',
          }}>
            {error}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button className="btn btn-ghost" onClick={close}>
            Cancel
          </button>
          <button
            className="btn btn-danger"
            onClick={handleRun}
            disabled={!expType}
          >
            ⚡ Execute Experiment
          </button>
        </div>
      </div>
    </div>
  )
}

function delay(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms))
}
