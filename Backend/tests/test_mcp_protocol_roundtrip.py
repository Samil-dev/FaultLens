"""
Real MCP protocol round-trip test.

Unlike test_mcp_tools.py (which calls the Python functions behind the MCP
tools directly), this test spawns app.mcp.server as an actual subprocess —
the same command/args/cwd shape .bob/mcp.json declares — and talks to it
over stdio using the real `mcp` SDK client. This is the strongest available
verification that the MCP server genuinely speaks the protocol correctly:
it does not call FaultLens's Python functions in-process at all, only the
wire protocol a real Bob (or any other MCP-compatible) agent would use.

No external credentials or network access are required — MCP over stdio is
a local subprocess protocol, so this is fully real and always executable in
this environment (unlike a real IBM Bob HTTP connection, which is not).
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def _run_roundtrip(system_id: str, db_path: str) -> dict:
    from mcp import types
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    env = dict(os.environ)
    env["CODETWIN_DATABASE_PATH"] = db_path

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.server"],
        cwd=str(BACKEND_DIR),
        env=env,
    )

    results: dict = {}

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init_result = await session.initialize()
            results["server_name"] = init_result.server_info.name

            tools_result = await session.list_tools()
            results["tool_names"] = sorted(t.name for t in tools_result.tools)

            # "Before" call — proves the context genuinely changes because
            # of the experiment, not that it was always populated: this
            # system has never been persisted yet at this point.
            before_result = await session.call_tool(
                "faultlens_get_context", {"system_id": system_id}
            )
            before_content = before_result.content[0]
            results["context_before"] = (
                json.loads(before_content.text) if isinstance(before_content, types.TextContent) else None
            )

            system = {
                "id": system_id,
                "name": "Protocol Round-Trip System",
                "nodes": [
                    {"id": "gw", "name": "Gateway", "node_type": "gateway"},
                    {"id": "svc", "name": "Service", "node_type": "service"},
                ],
                "dependencies": [{"source": "gw", "target": "svc", "type": "depends_on"}],
            }
            experiment = {
                "id": f"exp-{system_id}",
                "system_id": system_id,
                "target_node": "gw",
                "type": "service_down",
                "duration_seconds": 30,
            }

            run_result = await session.call_tool(
                "chaos_run_experiment", {"system": system, "experiment": experiment}
            )
            run_content = run_result.content[0]
            results["run_data"] = (
                json.loads(run_content.text) if isinstance(run_content, types.TextContent) else None
            )

            context_result = await session.call_tool(
                "faultlens_get_context", {"system_id": system_id}
            )
            context_content = context_result.content[0]
            results["context"] = (
                json.loads(context_content.text) if isinstance(context_content, types.TextContent) else None
            )

            unknown_result = await session.call_tool(
                "faultlens_get_context", {"system_id": "definitely-does-not-exist"}
            )
            unknown_content = unknown_result.content[0]
            results["unknown_context"] = (
                json.loads(unknown_content.text) if isinstance(unknown_content, types.TextContent) else None
            )

    return results


@pytest.mark.mcp_protocol
def test_mcp_server_speaks_the_real_protocol_and_context_reflects_the_run():
    """
    Spawns the real MCP server subprocess, over the real stdio transport,
    and drives it exclusively through MCP tool calls — no in-process
    function calls, no faked transport.
    """

    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
    tmp.close()

    results = asyncio.run(_run_roundtrip("sys-mcp-protocol-test", tmp.name))

    assert results["server_name"] == "FaultLens"
    assert results["tool_names"] == [
        "chaos_get_resilience_analysis",
        "chaos_run_experiment",
        "chaos_suggest_next_experiment",
        "faultlens_get_context",
    ]

    # Before the experiment, this system has never been persisted — a real,
    # honest "not found" from the same session, not a placeholder.
    assert "error" in results["context_before"]

    run_data = results["run_data"]
    assert run_data["run"]["status"] == "completed"
    assert run_data["ai_analysis"]["status"] == "available"

    # This is the real proof: faultlens_get_context, called as a *separate*
    # tool call over the same session, reflects the experiment that was
    # just run via chaos_run_experiment — proving the MCP tool actually
    # persisted real data, not something this test fabricated.
    context = results["context"]
    assert context["system_name"] == "Protocol Round-Trip System"
    assert context["run_id"] == run_data["run"]["id"]
    assert context["propagation_path"] == ["gw"]
    assert context["critical_nodes"] == ["gw"]

    assert results["unknown_context"]["error"]
