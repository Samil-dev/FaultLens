import { useEffect, useRef, useState } from 'react'
import { useStore } from '../../store/experimentStore'
import { runExperiment } from '../../services/api'
import type { ExperimentType } from '../../types/api'
import { EXPERIMENT_TYPES } from '../../constants/experimentTypes'
import { computeSettledNodeStates } from '../../utils/nodeStates'

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
    setNodeStatesBulk,
    resetNodeStates,
  } = useStore()

  const [expType, setExpType] = useState<ExperimentType>('service_down')
  const [duration, setDuration] = useState(30)
  const [error, setError] = useState<string | null>(null)
  const firstCardRef = useRef<HTMLButtonElement>(null)
  const isOpen = phase === 'configuring' && !!pendingExperiment

  // Autofocus the first control when the modal opens.
  useEffect(() => {
    if (isOpen) firstCardRef.current?.focus()
  }, [isOpen])

  // Close on Escape, unless an experiment is actively running.
  useEffect(() => {
    if (!isOpen) return
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && phase === 'configuring') close()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, phase])

  if (!isOpen) return null

  const targetNodeId = pendingExperiment!.target_node!
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

    // Captured so a stale response can't overwrite a *different* system's
    // state if the user switches systems (or imports a new one) while this
    // request is still in flight — see the guard right after the await.
    const systemAtStart = system
    const experimentId = `exp-${Date.now()}`

    const request = {
      system: systemAtStart,
      experiment: {
        id: experimentId,
        system_id: systemAtStart.id,
        target_node: pendingExperiment.target_node,
        type: expType,
        duration_seconds: duration,
      },
    }

    try {
      const response = await runExperiment(request)

      if (useStore.getState().system.id !== systemAtStart.id) {
        // The active system changed mid-request. Discard this result rather
        // than applying it to whatever system is active now — the user
        // already navigated away, so silently dropping it (not surfacing an
        // error) is the correct, expected behavior.
        return
      }

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

      if (useStore.getState().system.id !== systemAtStart.id) return

      // Settle on the exact same final frame History restores via
      // viewResult() — one shared computation, so a freshly-completed run
      // and a historical replay of it always look identical.
      setNodeStatesBulk(computeSettledNodeStates(systemAtStart, data))

      // Store results
      setLastResult(data)
      pushHistory(data)
      setPhase('done')
      setPendingExperiment(null)

    } catch (err) {
      if (useStore.getState().system.id !== systemAtStart.id) return
      const msg = err instanceof Error ? err.message : 'Unknown error'
      setError(msg)
      setPhase('configuring')
      resetNodeStates()
    }
  }

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && close()}>
      <div className="modal-box" role="dialog" aria-modal="true" aria-labelledby="experiment-modal-title" style={{ width: 520 }}>
        <div className="modal-title" id="experiment-modal-title">
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

        {/* Experiment type — professional experiment cards, one per backend-supported scenario */}
        <div className="form-group">
          <label className="form-label" id="experiment-type-label">Failure Scenario</label>
          <div
            role="radiogroup"
            aria-labelledby="experiment-type-label"
            style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}
          >
            {EXPERIMENT_TYPES.map((t, i) => {
              const selected = expType === t.value
              return (
                <button
                  key={t.value}
                  ref={i === 0 ? firstCardRef : undefined}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => setExpType(t.value)}
                  title={`Simulates: ${t.simulates}\nTests: ${t.tests}\nObserve: ${t.observe}`}
                  style={{
                    textAlign: 'left',
                    background: selected ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                    border: `1px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
                    borderRadius: 'var(--radius-md)',
                    padding: '8px 10px',
                    cursor: 'pointer',
                    color: 'inherit',
                    font: 'inherit',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                    <span>{t.icon}</span>
                    <span style={{ fontSize: 11, fontWeight: 700, color: selected ? 'var(--accent)' : 'var(--text-primary)' }}>
                      {t.label}
                    </span>
                  </div>
                  <p style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.4 }}>{t.simulates}</p>
                </button>
              )
            })}
          </div>
          <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, lineHeight: 1.5 }}>
            <strong style={{ color: 'var(--text-secondary)' }}>Tests: </strong>
            {EXPERIMENT_TYPES.find((t) => t.value === expType)?.tests}
            {' '}
            <strong style={{ color: 'var(--text-secondary)' }}>Observe: </strong>
            {EXPERIMENT_TYPES.find((t) => t.value === expType)?.observe}
          </p>
        </div>

        {/* Duration */}
        <div className="form-group">
          <label className="form-label" htmlFor="experiment-duration-input">Duration (seconds)</label>
          <input
            id="experiment-duration-input"
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
          background: 'rgba(245,158,11,0.08)',
          border: '1px solid rgba(245,158,11,0.2)',
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
            background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.25)',
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
