from pathlib import Path
import sys


# Ensure Backend is available on sys.path when MCP loads
# this file directly through `mcp dev`.
BACKEND_DIR = Path(__file__).resolve().parents[2]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from mcp.server import MCPServer

from app.mcp.tools import (
    get_resilience_analysis,
    run_chaos_experiment,
    suggest_next_experiment,
)


mcp = MCPServer(
    "CodeTwin ChaosLab",
)


@mcp.tool()
def chaos_run_experiment(
    system: dict,
    experiment: dict,
) -> dict:
    """
    Run a simulated chaos experiment in CodeTwin.

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
) -> dict:
    """
    Suggest the next experiment based on
    deterministic resilience evidence.
    """

    return suggest_next_experiment(
        analysis=analysis,
    )


if __name__ == "__main__":
    mcp.run()