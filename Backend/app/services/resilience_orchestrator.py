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


# Mirrors the Literal["service_down", "latency_spike", "resource_exhaustion",
# "traffic_spike"] used across the experiment models. Order matters: it's
# the cycling order _next_experiment_type() walks through per target node.
_EXPERIMENT_TYPES = ("service_down", "latency_spike", "resource_exhaustion", "traffic_spike")


def _tested_types_by_node(history: list[dict]) -> dict[str, set[str]]:
    """
    Maps each node id to the set of experiment types already run against it,
    from a system's persisted experiment history. Empty dict when no history
    is available — every helper below degrades to today's simpler behavior
    in that case.
    """

    tested: dict[str, set[str]] = {}
    for result in history:
        run = result.get("run", {})
        node = run.get("target_node")
        exp_type = run.get("type")
        if node and exp_type:
            tested.setdefault(node, set()).add(exp_type)
    return tested


def _best_candidate(
    candidates: list,
    last_target_node: str | None,
    tested_nodes: set[str],
) -> str:
    """
    Picks the best follow-up target from `candidates` (failed_recoveries or
    critical_nodes, in the order the analysis returned them):

    1. A candidate that has never been tested at all, other than the one
       just tested — the strongest possible alternative, since it's real
       unexplored evidence rather than a guess.
    2. Any candidate other than the one just tested (today's behavior).
    3. The first candidate, if every one of them is the node just tested.

    `tested_nodes` is empty when no history is available, so step 1 never
    finds a match and this degrades exactly to the pre-existing "any
    candidate other than the last one" behavior.
    """

    never_tested = [c for c in candidates if c != last_target_node and c not in tested_nodes]
    if never_tested:
        return never_tested[0]

    for candidate in candidates:
        if candidate != last_target_node:
            return candidate

    return candidates[0]


def _next_experiment_type(target_node: str, tested_types_by_node: dict[str, set[str]]) -> str:
    """
    Picks the first experiment type in _EXPERIMENT_TYPES that hasn't already
    been run against `target_node`, so a follow-up experiment exercises new
    ground instead of always re-suggesting service_down. Falls back to
    service_down (re-validation) once every type has been tried on this
    node. With no history, this always returns "service_down" — identical
    to the previous hardcoded behavior.
    """

    already_tested = tested_types_by_node.get(target_node, set())
    for experiment_type in _EXPERIMENT_TYPES:
        if experiment_type not in already_tested:
            return experiment_type
    return _EXPERIMENT_TYPES[0]


def suggest_next_experiment(
    analysis: dict,
    last_target_node: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    """
    Suggests a logical next experiment based on
    the deterministic resilience analysis.

    `last_target_node`, when provided, is the node the experiment that
    produced this analysis already targeted — used to avoid recommending an
    immediate repeat of the same experiment when the analysis offers a real
    alternative.

    `history`, when provided, is this system's past experiment results
    (most recent first, as returned by PersistenceService.list_experiments)
    — real, already-persisted data, never fabricated. It's used for two
    things: preferring a target node that's never been tested at all over
    one that merely isn't the immediate last target, and varying the
    suggested experiment *type* to one not yet tried on that node instead
    of always defaulting to service_down. Omitting it (or passing an empty
    list) preserves the exact pre-existing behavior — this never changes
    *which* recommendation branch is chosen, only which node/type within
    that branch is suggested.

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

    tested_types_by_node = _tested_types_by_node(history or [])
    tested_nodes = set(tested_types_by_node.keys())

    if failed_recoveries:
        target_node = _best_candidate(failed_recoveries, last_target_node, tested_nodes)
        experiment_type = _next_experiment_type(target_node, tested_types_by_node)

        return {
            "recommendation_type": "recovery_validation",
            "suggested_experiment": {
                "type": experiment_type,
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
            target_node = _best_candidate(critical_nodes, last_target_node, tested_nodes)
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

        experiment_type = _next_experiment_type(target_node, tested_types_by_node)

        return {
            "recommendation_type": "critical_dependency",
            "suggested_experiment": {
                "type": experiment_type,
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