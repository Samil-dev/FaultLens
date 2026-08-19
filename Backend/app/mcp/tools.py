"""
MCP tool entry points for FaultLens.

The actual business logic lives in app.services.resilience_orchestrator so it
has a single implementation shared by both the MCP server and (potentially)
other internal callers — this module only re-exports it under the tool names
expected by app.mcp.server, adding MCP-specific concerns (persistence,
context assembly) that a bare orchestration call shouldn't own.
"""

import logging

from app.ai.context_builder import build_context
from app.models.experiment_request import ExperimentRequest
from app.models.experiment_response import ExperimentRunData
from app.models.resilience_analysis import ResilienceAnalysis
from app.models.resilience_score import ResilienceScore
from app.models.simulation_run import SimulationRun
from app.services.ai_analysis_service import AIAnalysisService
from app.services.persistence_service import PersistenceService
from app.services.resilience_orchestrator import (
    get_resilience_analysis,
    run_chaos_experiment as _run_chaos_experiment,
    suggest_next_experiment as _suggest_next_experiment,
)

logger = logging.getLogger(__name__)

__all__ = [
    "get_resilience_analysis",
    "get_faultlens_context",
    "run_chaos_experiment",
    "suggest_next_experiment",
]

_get_resilience_analysis = get_resilience_analysis


def _record_activity(tool_name: str, system_id: str | None = None) -> None:
    """
    Best-effort activity recording — a logging hiccup here must never break
    an actual MCP tool call. This is the real, verifiable signal
    GET /api/mcp/status (and the frontend's "IBM Bob via MCP" indicator)
    is built on: MCP runs over a separate stdio subprocess with no other
    channel back to whatever process serves the REST API, so a real
    invocation of one of these functions is the only honest evidence that
    an MCP client has actually used FaultLens.
    """
    try:
        PersistenceService().record_mcp_activity(tool_name, system_id)
    except Exception:
        logger.exception("Failed to record MCP activity for tool '%s'", tool_name)


def get_resilience_analysis(system: dict, experiment: dict) -> dict:
    """
    Thin wrapper around resilience_orchestrator.get_resilience_analysis that
    additionally records MCP activity — see _record_activity().
    """
    _record_activity("chaos_get_resilience_analysis", system.get("id") if isinstance(system, dict) else None)
    return _get_resilience_analysis(system=system, experiment=experiment)


def run_chaos_experiment(system: dict, experiment: dict) -> dict:
    """
    Thin wrapper around resilience_orchestrator.run_chaos_experiment that
    additionally persists the system and the resulting run, and computes an
    AIInsight for it grounded in the same FaultLensContext pipeline — this
    is what POST /api/experiments/run also does, so an experiment triggered
    by an external Bob agent via MCP becomes real, retrievable history:
    later faultlens_get_context / chaos_suggest_next_experiment calls (and
    FaultLens's own UI History) will see it, exactly like an experiment run
    from the FaultLens UI.

    Persistence/AI-analysis failures never discard the underlying chaos
    experiment result — the same "don't let a secondary concern break the
    experiment" guarantee POST /api/experiments/run makes.
    """

    _record_activity("chaos_run_experiment", system.get("id") if isinstance(system, dict) else None)

    result = _run_chaos_experiment(system=system, experiment=experiment)

    try:
        request = ExperimentRequest(system=system, experiment=experiment)
        run = SimulationRun(**result["run"])
        analysis = ResilienceAnalysis(**result["analysis"])
        score = ResilienceScore(**result["resilience_score"])

        persistence = PersistenceService()
        history = persistence.list_experiments(request.system.id)

        context = build_context(
            system=request.system,
            experiment=request.experiment,
            run=run,
            analysis=analysis,
            resilience_score=score,
            history=history,
        )

        ai_insight = AIAnalysisService().analyze(
            analysis,
            experiment_type=request.experiment.type,
            target_node=request.experiment.target_node,
            context=context,
        )

        run_data = ExperimentRunData(
            run=run,
            events=result["events"],
            comparisons=result["comparisons"],
            resilience_score=score,
            analysis=analysis,
            ai_analysis=ai_insight,
        )

        persistence.save_system(request.system)
        persistence.save_experiment(request.system.id, run_data)

        result["ai_analysis"] = ai_insight.model_dump(mode="json")
    except Exception:
        logger.exception("Failed to persist MCP-triggered experiment or compute its AIInsight")

    return result


def suggest_next_experiment(
    analysis: dict,
    last_target_node: str | None = None,
    system_id: str | None = None,
) -> dict:
    """
    Thin wrapper around resilience_orchestrator.suggest_next_experiment that
    additionally accepts `system_id` so an MCP caller can get a
    history-aware suggestion (preferring never-tested nodes, varying the
    experiment type) without having to fetch and pass the history itself —
    mirrors POST /api/experiments/suggest-next's system_id query param.
    """

    _record_activity("chaos_suggest_next_experiment", system_id)

    history = (
        [result.model_dump(mode="json") for result in PersistenceService().list_experiments(system_id)]
        if system_id
        else None
    )
    return _suggest_next_experiment(
        analysis=analysis,
        last_target_node=last_target_node,
        history=history,
    )


def get_faultlens_context(system_id: str) -> dict:
    """
    Returns the structured FaultLensContext for a persisted system: its
    topology, the most recent experiment run (propagation, metrics,
    resilience analysis), and a compact trend summary of past experiments —
    the same evidence FaultLens's in-app AI provider is grounded in.

    This is what makes Bob's reasoning (when called via MCP) informed by the
    whole Core Workflow instead of a single isolated result. Returns an
    error dict — never raises — if the system doesn't exist, so a calling
    agent gets an actionable message instead of a protocol-level failure.
    """

    _record_activity("faultlens_get_context", system_id)

    persistence = PersistenceService()
    system = persistence.get_system(system_id)
    if system is None:
        return {"error": f"No system found with id '{system_id}'"}

    history = persistence.list_experiments(system_id)
    latest = history[0] if history else None

    context = build_context(
        system=system,
        run=latest.run if latest else None,
        analysis=latest.analysis if latest else None,
        resilience_score=latest.resilience_score if latest else None,
        history=history[1:] if latest else history,
    )
    return context.model_dump(mode="json")
