from app.models.experiment_request import ExperimentRequest
from app.services.chaos_service import ChaosService
from app.services.resilience_analysis_service import (
    ResilienceAnalysisService,
)
from app.services.resilience_service import ResilienceService


def run_chaos_experiment(
    system: dict,
    experiment: dict,
) -> dict:
    """
    Runs a simulated chaos experiment in FaultLens.

    Returns the complete deterministic result:
    simulation run, events, metric comparisons,
    resilience score, and resilience analysis.
    """

    request = ExperimentRequest(
        system=system,
        experiment=experiment,
    )

    run, events, comparisons = ChaosService().run_experiment(
        request.system,
        request.experiment,
    )

    resilience_score = ResilienceService().calculate_score(
        comparisons,
        len(run.affected_nodes),
        len(request.system.nodes),
    )

    analysis = ResilienceAnalysisService().analyze(
        experiment=request.experiment,
        run=run,
        comparisons=comparisons,
        score=resilience_score,
        total_nodes=len(request.system.nodes),
    )

    return {
        "experiment": request.experiment.model_dump(mode="json"),
        "run": run.model_dump(mode="json"),
        "events": [
            event.model_dump(mode="json")
            for event in events
        ],
        "comparisons": [
            comparison.model_dump(mode="json")
            for comparison in comparisons
        ],
        "resilience_score": resilience_score.model_dump(
            mode="json"
        ),
        "analysis": analysis.model_dump(mode="json"),
    }


def get_resilience_analysis(
    system: dict,
    experiment: dict,
) -> dict:
    """
    Runs a chaos experiment and returns the
    resilience-focused analysis.
    """

    result = run_chaos_experiment(
        system=system,
        experiment=experiment,
    )

    return {
        "experiment": result["experiment"],
        "resilience_score": result["resilience_score"],
        "analysis": result["analysis"],
    }


def _first_other(candidates: list, exclude: str | None) -> str:
    """
    Returns the first candidate that isn't `exclude` (the node just tested),
    so a follow-up suggestion doesn't just repeat the last experiment when a
    genuine alternative is available. Falls back to the first candidate if
    every one of them is the excluded node.
    """

    for candidate in candidates:
        if candidate != exclude:
            return candidate

    return candidates[0]


def suggest_next_experiment(
    analysis: dict,
    last_target_node: str | None = None,
) -> dict:
    """
    Suggests a logical next experiment based on
    the deterministic resilience analysis.

    `last_target_node`, when provided, is the node the experiment that
    produced this analysis already targeted — used only to avoid
    recommending an immediate repeat of the same experiment when the
    analysis offers a real alternative. It never changes *which* branch of
    the recommendation is chosen, only *which node within that branch* is
    suggested.

    This does not attempt to replace IBM Bob's reasoning.
    It provides structured evidence that Bob can use.
    """

    impact = analysis.get("impact", {})
    recovery = analysis.get("recovery", {})
    risk = analysis.get("risk", {})

    critical_nodes = impact.get(
        "critical_nodes",
        [],
    )

    failed_recoveries = recovery.get(
        "failed_recoveries",
        [],
    )

    risk_level = risk.get(
        "level",
        "unknown",
    )

    if failed_recoveries:
        target_node = _first_other(failed_recoveries, last_target_node)

        return {
            "recommendation_type": "recovery_validation",
            "suggested_experiment": {
                "type": "service_down",
                "target_node": target_node,
                "duration_seconds": 30,
            },
            "reason": (
                f"Node '{target_node}' failed to recover "
                "successfully and should be tested again."
            ),
            "risk_level": risk_level,
        }

    if critical_nodes:
        other_critical_nodes = [n for n in critical_nodes if n != last_target_node]

        if other_critical_nodes:
            target_node = other_critical_nodes[0]
            reason = (
                f"Node '{target_node}' was identified as a "
                "critical component in the resilience analysis."
            )
        else:
            # The only critical node on record is the one just tested —
            # still worth re-validating, but say so honestly instead of
            # phrasing it as if a new dependency had been discovered.
            target_node = critical_nodes[0]
            reason = (
                f"Node '{target_node}' remains the only critical component "
                "identified so far. Re-testing it will confirm whether its "
                "resilience has improved."
            )

        return {
            "recommendation_type": "critical_dependency",
            "suggested_experiment": {
                "type": "service_down",
                "target_node": target_node,
                "duration_seconds": 30,
            },
            "reason": reason,
            "risk_level": risk_level,
        }

    if risk_level in {"high", "critical"}:
        return {
            "recommendation_type": "high_risk_follow_up",
            "suggested_experiment": None,
            "reason": (
                "The system remains at elevated risk and "
                "requires additional resilience validation. "
                "A specific target node could not be determined "
                "from the current analysis."
            ),
            "risk_level": risk_level,
        }

    return {
        "recommendation_type": "no_immediate_follow_up",
        "suggested_experiment": None,
        "reason": (
            "The current analysis did not identify a "
            "clear high-priority follow-up experiment."
        ),
        "risk_level": risk_level,
    }