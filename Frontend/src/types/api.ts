// ─── Primitives ──────────────────────────────────────────────────────────────

export type NodeStatus = 'healthy' | 'degraded' | 'failed' | 'recovering'
export type RiskLevel = 'low' | 'moderate' | 'high' | 'critical'
export type ResilienceRating = 'excellent' | 'good' | 'moderate' | 'poor' | 'critical'
export type RecoveryStatus = 'pending' | 'recovering' | 'recovered' | 'failed'
export type ExperimentType = 'service_down' | 'latency_spike' | 'resource_exhaustion' | 'traffic_spike'
export type DependencyType = 'depends_on' | 'communicates_with'
export type RecommendationPriority = 'low' | 'medium' | 'high'
export type EventType = 'failure_injected' | 'node_degraded' | 'node_failed' | 'node_recovered'
export type SimulationStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

// ─── System model ─────────────────────────────────────────────────────────────

export interface SystemNode {
  id: string
  name: string
  node_type: string
  status: NodeStatus
  description?: string | null
}

export interface Dependency {
  source: string
  target: string
  type: DependencyType
}

export interface System {
  id: string
  name: string
  nodes: SystemNode[]
  dependencies: Dependency[]
}

// ─── Experiment model ─────────────────────────────────────────────────────────

export interface Experiment {
  id: string
  system_id: string
  target_node: string
  type: ExperimentType
  duration_seconds: number
}

// ─── Request ──────────────────────────────────────────────────────────────────

export interface ExperimentRequest {
  system: System
  experiment: Experiment
}

// ─── Simulation results ───────────────────────────────────────────────────────

export interface Recovery {
  node_id: string
  recovery_status: RecoveryStatus
  recovery_time_seconds: number | null
}

export interface SimulationRun {
  id: string
  experiment_id: string
  type: ExperimentType
  target_node: string
  // Configured duration, in seconds, that produced this run — real,
  // deterministic input to propagation depth, recovery time, and metric
  // severity (see Backend/app/chaos/duration_model.py). Null only for
  // runs persisted before this field existed.
  duration_seconds: number | null
  status: SimulationStatus
  started_at: string | null
  finished_at: string | null
  affected_nodes: string[]
  created_at: string
  recoveries: Recovery[]
}

export interface SimulationEvent {
  id: string
  run_id: string
  node_id: string
  event_type: EventType
  severity: number
  timestamp: string
}

export interface MetricComparison {
  node_id: string
  cpu_usage_delta: number
  memory_usage_delta: number
  latency_delta_ms: number
  error_rate_delta: number
}

// ─── Analysis models ──────────────────────────────────────────────────────────

export interface ResilienceScore {
  score: number
  rating: ResilienceRating
  affected_nodes: number
  total_nodes: number
}

export interface ImpactAnalysis {
  blast_radius: number
  affected_nodes: number
  total_nodes: number
  critical_nodes: string[]
  average_metric_impact: number
}

export interface RecoveryAnalysis {
  recovered_nodes: number
  total_recovery_nodes: number
  average_recovery_seconds: number
  max_recovery_seconds: number
  failed_recoveries: string[]
}

export interface RiskAnalysis {
  level: RiskLevel
  reason: string
}

export interface Recommendation {
  title: string
  description: string
  priority: RecommendationPriority
}

export interface ResilienceAnalysis {
  impact: ImpactAnalysis
  recovery: RecoveryAnalysis
  risk: RiskAnalysis
  recommendations: Recommendation[]
}

export interface AIAnalysis {
  summary: string
  root_cause: string
  risk_interpretation: string
  recommendations: string[]
  confidence: number
  provider: string
}

// An AI provider attempt is never assumed to succeed — `status` says
// exactly what happened, and `analysis` is only ever populated when it's
// 'available'. Every other status carries a human-readable `message`
// instead, which must be rendered as an honest status explanation, never
// as if it were a real AI-generated response.
export type AIInsightStatus = 'available' | 'not_configured' | 'unavailable' | 'error'

export interface AIInsight {
  status: AIInsightStatus
  provider: string
  analysis: AIAnalysis | null
  message: string | null
}

// ─── API response shape ───────────────────────────────────────────────────────

export interface ExperimentRunData {
  run: SimulationRun
  events: SimulationEvent[]
  comparisons: MetricComparison[]
  resilience_score: ResilienceScore
  analysis: ResilienceAnalysis
  ai_analysis: AIInsight
}

// ─── Scenario comparison ──────────────────────────────────────────────────────

export interface ScenarioComparisonRequest {
  run_ids: string[]
}

export interface ScenarioComparison {
  runs: ExperimentRunData[]
}

export interface ExperimentApiResponse {
  success: boolean
  data: ExperimentRunData | null
  error: { message: string; code?: string } | null
}

export interface HealthResponse {
  success: boolean
  data: {
    status: string
    services: string
  }
  error: null
}

// ─── MCP status ────────────────────────────────────────────────────────────────
// Reflects only what's actually observable from the REST API: whether the MCP
// server module is importable in this backend, and the most recent real MCP
// tool invocation recorded (if any). There is no live "connected" boolean —
// MCP runs over a separate stdio subprocess with no channel back to the
// process serving this API, so a fabricated one would not be honest.

export interface McpActivity {
  tool_name: string
  system_id: string | null
  called_at: string
  seconds_ago: number
}

export interface McpStatusResponse {
  success: boolean
  data: {
    server_available: boolean
    last_activity: McpActivity | null
  }
  error: null
}

// ─── Next experiment suggestion ────────────────────────────────────────────────

export type NextExperimentRecommendationType =
  | 'recovery_validation'
  | 'critical_dependency'
  | 'high_risk_follow_up'
  | 'no_immediate_follow_up'

export interface SuggestedExperiment {
  type: ExperimentType
  target_node: string
  duration_seconds: number
}

export interface NextExperimentSuggestion {
  recommendation_type: NextExperimentRecommendationType
  suggested_experiment: SuggestedExperiment | null
  reason: string
  risk_level: string
}
