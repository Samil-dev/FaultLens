import { useEffect, useState } from 'react'
import { useStore } from '../../store/experimentStore'
import { suggestNextExperiment } from '../../services/api'
import type { NextExperimentSuggestion as Suggestion, ResilienceAnalysis } from '../../types/api'
import { EXPERIMENT_TYPE_LABEL } from '../../utils/format'

type State =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; suggestion: Suggestion }

export function NextExperimentSuggestion({ analysis }: { analysis: ResilienceAnalysis }) {
  const { system, setPendingExperiment, setPhase } = useStore()
  const [state, setState] = useState<State>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    setState({ status: 'loading' })
    suggestNextExperiment(analysis)
      .then((suggestion) => { if (!cancelled) setState({ status: 'ready', suggestion }) })
      .catch((err) => {
        if (!cancelled) setState({
          status: 'error',
          message: err instanceof Error ? err.message : 'Could not reach the backend.',
        })
      })
    return () => { cancelled = true }
  }, [analysis])

  function runSuggested(exp: NonNullable<Suggestion['suggested_experiment']>) {
    setPendingExperiment({
      system_id: system.id,
      target_node: exp.target_node,
      type: exp.type,
      duration_seconds: exp.duration_seconds,
    })
    setPhase('configuring')
  }

  return (
    <div className="panel-section">
      <p className="panel-section-title">Recommended Next Experiment</p>

      {state.status === 'loading' && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0' }}>
          <span className="spinner" style={{ width: 12, height: 12, borderWidth: 1.5 }} />
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Evaluating follow-up experiments…</span>
        </div>
      )}

      {state.status === 'error' && (
        <p className="value-na" style={{ fontSize: 11 }}>
          Unavailable — {state.message}
        </p>
      )}

      {state.status === 'ready' && (() => {
        const { suggestion } = state
        const targetName = suggestion.suggested_experiment
          ? system.nodes.find((n) => n.id === suggestion.suggested_experiment!.target_node)?.name
            ?? suggestion.suggested_experiment.target_node
          : null

        return (
          <>
            <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: suggestion.suggested_experiment ? 10 : 0 }}>
              {suggestion.reason}
            </p>

            {suggestion.suggested_experiment ? (
              <div style={{
                background: 'var(--bg-elevated)', border: '1px solid var(--border-bright)',
                borderRadius: 'var(--radius-md)', padding: '10px 12px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontSize: 12, fontWeight: 700 }}>
                    {EXPERIMENT_TYPE_LABEL[suggestion.suggested_experiment.type] ?? suggestion.suggested_experiment.type}
                  </span>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                    {suggestion.suggested_experiment.duration_seconds}s
                  </span>
                </div>
                <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8 }}>
                  Target: <strong style={{ color: 'var(--text-primary)' }}>{targetName}</strong>
                </p>
                <button
                  className="btn btn-primary btn-sm"
                  style={{ width: '100%', justifyContent: 'center' }}
                  onClick={() => runSuggested(suggestion.suggested_experiment!)}
                >
                  ⚡ Run Suggested Experiment
                </button>
              </div>
            ) : null}
          </>
        )
      })()}
    </div>
  )
}
