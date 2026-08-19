"""
MCP tool entry points for FaultLens.

The actual business logic lives in app.services.resilience_orchestrator so it
has a single implementation shared by both the MCP server and (potentially)
other internal callers — this module only re-exports it under the tool names
expected by app.mcp.server.
"""

from app.ai.context_builder import build_context
from app.services.persistence_service import PersistenceService
from app.services.resilience_orchestrator import (
    get_resilience_analysis,
    run_chaos_experiment,
    suggest_next_experiment as _suggest_next_experiment,
)

__all__ = [
    "get_resilience_analysis",
    "get_faultlens_context",
    "run_chaos_experiment",
    "suggest_next_experiment",
]


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
