from pathlib import Path
import sys


# Ensure Backend is available on sys.path when MCP loads
# this file directly through `mcp dev`.
BACKEND_DIR = Path(__file__).resolve().parents[2]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from mcp.server import MCPServer

from app.mcp.tools import (
    get_faultlens_context,
    get_resilience_analysis,
    run_chaos_experiment,
    suggest_next_experiment,
)


mcp = MCPServer(
    "FaultLens",
)


@mcp.tool()
def chaos_run_experiment(
    system: dict,
    experiment: dict,
) -> dict:
    """
    Run a simulated chaos experiment in FaultLens.

    Returns:
    - simulation run
    - affected nodes
    - events
    - metric comparisons
    - resilience score
    - resilience analysis
    """

    return run_chaos_experiment(
        system=system,
        experiment=experiment,
    )


@mcp.tool()
def chaos_get_resilience_analysis(
    system: dict,
    experiment: dict,
) -> dict:
    """
    Analyze the resilience impact of a proposed
    chaos experiment.
    """

    return get_resilience_analysis(
        system=system,
        experiment=experiment,
    )


@mcp.tool()
def chaos_suggest_next_experiment(
    analysis: dict,
    last_target_node: str | None = None,
) -> dict:
    """
    Suggest the next experiment based on
    deterministic resilience evidence.
    """

    return suggest_next_experiment(
        analysis=analysis,
        last_target_node=last_target_node,
    )


@mcp.tool()
def faultlens_get_context(
    system_id: str,
) -> dict:
    """
    Get the structured FaultLens context for a system: its architecture,
    the most recent chaos experiment's propagation and resilience analysis,
    and a summary of its experiment history.

    This is the recommended entry point for Bob to understand a FaultLens
    system before explaining a result or recommending a next step — it
    carries the whole workflow's evidence, not just one isolated result.
    """

    return get_faultlens_context(
        system_id=system_id,
    )


if __name__ == "__main__":
    mcp.run()