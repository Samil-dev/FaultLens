"""
MCP tool entry points for FaultLens.

The actual business logic lives in app.services.resilience_orchestrator so it
has a single implementation shared by both the MCP server and (potentially)
other internal callers — this module only re-exports it under the tool names
expected by app.mcp.server.
"""

from app.services.resilience_orchestrator import (
    get_resilience_analysis,
    run_chaos_experiment,
    suggest_next_experiment,
)

__all__ = [
    "get_resilience_analysis",
    "run_chaos_experiment",
    "suggest_next_experiment",
]
