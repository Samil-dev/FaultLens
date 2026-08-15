import type {
  ExperimentRequest,
  ExperimentApiResponse,
  ExperimentRunData,
  HealthResponse,
  System,
} from '../types/api'

const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json() as Promise<T>
}

async function post<TBody, TResponse>(path: string, body: TBody): Promise<TResponse> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`POST ${path} → ${res.status}: ${text}`)
  }
  return res.json() as Promise<TResponse>
}

/** GET /api/health — check backend connectivity */
export function fetchHealth(): Promise<HealthResponse> {
  return get<HealthResponse>('/health')
}

/** POST /api/systems/ — validate + echo a System definition */
export function createSystem(system: System): Promise<{ success: boolean; data: System }> {
  return post('/systems/', system)
}

/** GET /api/systems/ — retrieve locally saved Digital Twins */
export function fetchSystems(): Promise<System[]> {
  return get<System[]>('/systems/')
}

/** POST /api/experiments/run — execute a chaos experiment */
export function runExperiment(request: ExperimentRequest): Promise<ExperimentApiResponse> {
  return post('/experiments/run', request)
}

/** GET /api/experiments/ — retrieve persisted experiment history */
export function fetchExperimentHistory(systemId: string): Promise<ExperimentRunData[]> {
  return get<ExperimentRunData[]>(`/experiments/?system_id=${encodeURIComponent(systemId)}`)
}
