import type { ExperimentType } from '../types/api'

export const EXPERIMENT_TYPE_LABEL: Record<ExperimentType, string> = {
  service_down:        'Service Down',
  latency_spike:       'Latency Spike',
  resource_exhaustion: 'Resource Exhaustion',
  traffic_spike:       'Traffic Spike',
}

export function formatTimestamp(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
