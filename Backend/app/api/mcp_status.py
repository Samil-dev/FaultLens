"""
Reports the real, observable state of FaultLens's MCP integration for the
frontend's "IBM Bob via MCP" indicator.

MCP itself runs over a separate stdio subprocess (app/mcp/server.py,
registered via .bob/mcp.json) with no other channel back to whatever
process is serving this REST API — so this endpoint cannot report a live
"is a client connected right now" boolean, because that information simply
doesn't cross the process boundary. What it CAN honestly report:

- `server_available`: whether app.mcp.server and its dependencies (the
  `mcp` package) actually import cleanly in this backend installation —
  a real capability check, not a liveness probe.
- `last_activity`: the most recent real MCP tool invocation recorded by
  app/mcp/tools.py's _record_activity(), if any has ever happened against
  this database. This is genuine evidence an MCP client has used FaultLens
  — not a fabricated "connected" flag.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.services.persistence_service import PersistenceService

router = APIRouter(
    prefix="/api/mcp",
    tags=["MCP"],
)


def _mcp_server_available() -> bool:
    try:
        import app.mcp.server  # noqa: F401
        return True
    except Exception:
        return False


@router.get("/status")
def get_mcp_status():
    last = PersistenceService().get_last_mcp_activity()

    last_activity = None
    if last is not None:
        called_at = datetime.fromisoformat(last["called_at"])
        seconds_ago = (datetime.now(timezone.utc) - called_at).total_seconds()
        last_activity = {
            "tool_name": last["tool_name"],
            "system_id": last["system_id"],
            "called_at": last["called_at"],
            "seconds_ago": max(0, round(seconds_ago)),
        }

    return {
        "success": True,
        "data": {
            "server_available": _mcp_server_available(),
            "last_activity": last_activity,
        },
        "error": None,
    }
