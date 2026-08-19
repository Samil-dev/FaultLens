from app.models.experiment import Experiment
from app.models.experiment_response import ExperimentRunData
from app.models.faultlens_context import FaultLensContext, HistoryEntrySummary
from app.models.next_experiment_suggestion import NextExperimentSuggestion
from app.models.resilience_analysis import ResilienceAnalysis
from app.models.resilience_score import ResilienceScore
from app.models.simulation_run import SimulationRun
from app.models.system import System

# How many past runs to include in the context. Keeps prompts (and MCP
# payloads) bounded regardless of how long a system's history grows, while
# still giving a provider enough of a trend to reason about.
_MAX_HISTORY_ENTRIES = 10


def _history_summary(past_runs: list[ExperimentRunData]) -> list[HistoryEntrySummary]:
    return [
        HistoryEntrySummary(
            run_id=result.run.id,
            target_node=result.run.target_node,
            experiment_type=result.run.type,
            resilience_score=result.resilience_score.score,
            risk_level=result.analysis.risk.level,
            created_at=result.run.created_at.isoformat(),
        )
        for result in past_runs[:_MAX_HISTORY_ENTRIES]
    ]


def build_context(
    system: System,
    experiment: Experiment | None = None,
    run: SimulationRun | None = None,
    analysis: ResilienceAnalysis | None = None,
    resilience_score: ResilienceScore | None = None,
    history: list[ExperimentRunData] | None = None,
    previous_recommendation: dict | None = None,
) -> FaultLensContext:
    """
    Assembles the structured evidence FaultLens hands to an AI provider or
    to an external Bob agent (via MCP), from real data only:

    - `system`: the imported architecture (always required).
    - `experiment`: the experiment being designed/run, if any.
    - `run` / `analysis` / `resilience_score`: the outcome of the experiment
      that just ran, if any (kept as separate pieces rather than a full
      ExperimentRunData so this can be called *before* an AIInsight for that
      same run exists yet — see app/api/experiment.py).
    - `history`: past completed runs for this system, most recent first —
      used only to build a compact trend summary, never sent in full.
    - `previous_recommendation`: the last suggest-next-experiment output for
      this system, if one was computed.
    """

    context = FaultLensContext(
        system_id=system.id,
        system_name=system.name,
        nodes=system.nodes,
        dependencies=system.dependencies,
        history=_history_summary(history or []),
    )

    if experiment is not None:
        context.target_node = experiment.target_node
        context.experiment_type = experiment.type
        context.duration_seconds = experiment.duration_seconds

    if run is not None:
        context.target_node = context.target_node or run.target_node
        context.experiment_type = context.experiment_type or run.type
        context.run_id = run.id
        context.run_status = run.status
        context.affected_nodes = list(run.affected_nodes)
        context.propagation_path = [run.target_node, *run.affected_nodes]
        context.recoveries = list(run.recoveries)

    if resilience_score is not None:
        context.resilience_score = resilience_score

    if analysis is not None:
        context.analysis = analysis
        context.critical_nodes = list(analysis.impact.critical_nodes)

    if previous_recommendation is not None:
        context.previous_recommendation = NextExperimentSuggestion(**previous_recommendation)

    return context
