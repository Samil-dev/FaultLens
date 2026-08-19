"""
A real MCP client for FaultLens — not a mock, not a simulation.

Spawns app.mcp.server exactly as .bob/mcp.json declares (same command/args/
cwd shape) and drives it over the real MCP stdio protocol using the `mcp`
SDK's own client, exactly as a real Bob-compatible agent would. Useful for:

- Demoing the IBM Bob / MCP integration live: run this while the FaultLens
  UI is open (pointed at the same database) and watch the header's
  "IBM Bob" indicator go from "Not connected" to "Active via MCP" — real
  evidence, not a toggled flag.
- Playwright verification (see Frontend/e2e/mcp-integration.spec.ts) of the
  same thing, automated.

Usage:
    venv\\Scripts\\python.exe scripts\\mcp_demo_client.py [system_id]

Requires no external credentials — MCP over stdio is a local subprocess
protocol. Set CODETWIN_DATABASE_PATH before running if you want this to
target a specific database (e.g. the one your `uvicorn` dev server is
already using, so the change is visible in the running UI).
"""

import asyncio
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def main(system_id: str) -> dict:
    from mcp import types
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.server"],
        cwd=str(BACKEND_DIR),
        env=dict(os.environ),
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            system = {
                "id": system_id,
                "name": "MCP Demo System",
                "nodes": [
                    {"id": "gateway", "name": "API Gateway", "node_type": "gateway"},
                    {"id": "checkout", "name": "Checkout Service", "node_type": "service"},
                    {"id": "db", "name": "Primary Database", "node_type": "database"},
                ],
                "dependencies": [
                    {"source": "gateway", "target": "checkout", "type": "depends_on"},
                    {"source": "checkout", "target": "db", "type": "depends_on"},
                ],
            }
            experiment = {
                "id": f"exp-{system_id}",
                "system_id": system_id,
                "target_node": "checkout",
                "type": "service_down",
                "duration_seconds": 30,
            }

            run_result = await session.call_tool(
                "chaos_run_experiment", {"system": system, "experiment": experiment}
            )
            run_content = run_result.content[0]
            run_data = (
                json.loads(run_content.text) if isinstance(run_content, types.TextContent) else {}
            )

            context_result = await session.call_tool(
                "faultlens_get_context", {"system_id": system_id}
            )
            context_content = context_result.content[0]
            context_data = (
                json.loads(context_content.text) if isinstance(context_content, types.TextContent) else {}
            )

            return {"run": run_data, "context": context_data}


if __name__ == "__main__":
    target_system_id = sys.argv[1] if len(sys.argv) > 1 else "sys-mcp-demo"
    result = asyncio.run(main(target_system_id))
    print(json.dumps(result, indent=2))
