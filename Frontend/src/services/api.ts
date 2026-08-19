import type {
  ExperimentRequest,
  ExperimentApiResponse,
  ExperimentRunData,
  HealthResponse,
  NextExperimentSuggestion,
  ResilienceAnalysis,
  ScenarioComparison,
  ScenarioComparisonRequest,
  System,
} from '../types/api'

const BASE = '/api'

/**
 * Extracts a clean, human-readable message from a non-ok response body.
 * The backend uses two different error shapes depending on where the
 * error originates:
 *  - `{ success: false, error: { message } }` — the app's own ValueError
 *    handler (app.main.value_error_handler), for errors raised inside an
 *    endpoint body.
 *  - `{ detail: [{ msg, ... }] }` (or `{ detail: "..." }`) — FastAPI's
 *    default shape for request-body validation errors (422), which is
 *    what Pydantic model_validator errors raised while parsing a request
 *    body actually surface as.
 * Falls back to the raw response text if neither shape matches, so an
 * unexpected error still shows *something* rather than nothing.
 */
function extractErrorMessage(text: string, status: number): string {
  try {
    const body = JSON.parse(text)
    if (body?.error?.message) return body.error.message
    if (Array.isArray(body?.detail)) {
      return body.detail
        .map((d: { msg?: string }) => d.msg?.replace(/^Value error,\s*/, '') ?? JSON.stringify(d))
        .join('; ')
    }
    if (typeof body?.detail === 'string') return body.detail
  } catch {
    // Not JSON — fall through to the raw text below.
  }
  return text.trim() || `Request failed with status ${status}`
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(extractErrorMessage(await res.text(), res.status))
  return res.json() as Promise<T>
}

async function post<TBody, TResponse>(path: string, body: TBody): Promise<TResponse> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(extractErrorMessage(await res.text(), res.status))
  }
  return res.json() as Promise<TResponse>
}

/** GET /api/health — check backend connectivity */
export function fetchHealth(): Promise<HealthResponse> {
  return get<HealthResponse>('/health')
}

/** POST /api/systems/ — validate + persist a System definition (imports/creates a digital twin) */
export function createSystem(
  system: System,
): Promise<{ success: boolean; data: System; error: { message: string; code?: string } | null }> {
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

/** POST /api/experiments/compare — retrieve two to four runs for side-by-side comparison */
export function compareExperiments(request: ScenarioComparisonRequest): Promise<ScenarioComparison> {
  return post<ScenarioComparisonRequest, ScenarioComparison>('/experiments/compare', request)
}

/**
 * POST /api/experiments/suggest-next — suggest a logical follow-up experiment
 * for a completed analysis. `lastTargetNode` (the node the analysis's own
 * experiment already targeted) lets the backend avoid immediately
 * re-suggesting that same node when a real alternative exists.
 */
export function suggestNextExperiment(
  analysis: ResilienceAnalysis,
  lastTargetNode?: string,
): Promise<NextExperimentSuggestion> {
  const query = lastTargetNode ? `?last_target_node=${encodeURIComponent(lastTargetNode)}` : ''
  return post<ResilienceAnalysis, NextExperimentSuggestion>(`/experiments/suggest-next${query}`, analysis)
}
