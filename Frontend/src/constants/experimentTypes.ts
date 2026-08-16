import type { ExperimentType } from '../types/api'

/**
 * Experiment templates — only the four types the backend actually
 * implements (see Backend/app/chaos/chaos_engine.py). Shared between the
 * "Chaos Experiments" sidebar overview and the run-experiment modal so the
 * two never drift out of sync.
 */
export const EXPERIMENT_TYPES: {
  value: ExperimentType
  label: string
  icon: string
  simulates: string
  tests: string
  observe: string
}[] = [
  {
    value: 'service_down',
    label: 'Service Down',
    icon: '🔴',
    simulates: 'A temporary, complete outage of the target node.',
    tests: 'Whether dependent services degrade gracefully when a dependency disappears entirely.',
    observe: 'Blast radius, which dependents fail, and recovery time once the node returns.',
  },
  {
    value: 'latency_spike',
    label: 'Latency Spike',
    icon: '⏱',
    simulates: 'A sharp increase in the target node’s response time.',
    tests: 'Whether timeouts, retries, and circuit breakers are tuned correctly downstream.',
    observe: 'How latency compounds across the dependency chain.',
  },
  {
    value: 'resource_exhaustion',
    label: 'Resource Exhaustion',
    icon: '📉',
    simulates: 'CPU and memory saturation on the target node.',
    tests: 'Whether the node degrades predictably under resource pressure instead of failing outright.',
    observe: 'Error rate and throughput as the node struggles to keep up.',
  },
  {
    value: 'traffic_spike',
    label: 'Traffic Spike',
    icon: '📶',
    simulates: 'A sudden surge in request volume against the target node.',
    tests: 'Whether the node sheds load gracefully instead of collapsing under demand.',
    observe: 'Error rate growth and whether the overload propagates upstream.',
  },
]
