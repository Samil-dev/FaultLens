# AI / IBM Bob Integration Architecture

This document describes exactly what's connected today, what's prepared but
not yet connected, and what's required to activate a real integration. It
exists to be read honestly — nothing here should be taken as a claim that
IBM Bob is fully integrated as an in-app AI provider, because it isn't yet.

## Two separate integration surfaces

FaultLens has two distinct places where "AI" and "Bob" show up, and they are
not the same thing:

1. **The in-app AI Insights panel** — FaultLens's own backend calls an
   `AIProvider` to interpret a completed experiment and shows the result in
   its UI (`RightPanel`, the "AI Insights" sidebar tab).
2. **The MCP server** — FaultLens's backend exposes its own orchestration
   logic (run an experiment, get a resilience analysis, suggest a next
   experiment, get the structured context of a system) as tools an external
   agent can call. This is the *reverse* direction: an agent connects
   **into** FaultLens, rather than FaultLens calling **out** to an agent.

**Surface 2 (MCP) is what's actually working today.** `.bob/mcp.json`
registers FaultLens's backend (`app/mcp/server.py`) as an MCP server. When a
Bob-compatible agent is configured to use it, it can call:

| Tool | What it returns |
|---|---|
| `chaos_run_experiment(system, experiment)` | The full deterministic simulation result. |
| `chaos_get_resilience_analysis(system, experiment)` | The resilience analysis for a proposed experiment. |
| `chaos_suggest_next_experiment(analysis, last_target_node?, system_id?)` | A follow-up recommendation; history-aware when `system_id` is supplied. |
| `faultlens_get_context(system_id)` | The full `FaultLensContext` for a system: topology, most recent run's propagation/metrics/resilience analysis, and a compact history trend. |

`faultlens_get_context` is the important one for the "Bob understands the
whole workflow, not just one isolated result" goal — it's built by
`app/ai/context_builder.py` from real, already-persisted data (see
`app/models/faultlens_context.py`), the same context the in-app provider's
prompt is grounded in.

`chaos_run_experiment`, called via MCP, persists the system and the result
(and computes an in-app `AIInsight` for it) exactly like
`POST /api/experiments/run` does — an experiment triggered by an external
Bob agent through MCP becomes real history immediately visible to a later
`faultlens_get_context` or `chaos_suggest_next_experiment` call, and to
FaultLens's own UI History.

**This surface is empirically verified, not just inspected**:
`tests/test_mcp_protocol_roundtrip.py` spawns `app.mcp.server` as a real
subprocess (the same `command`/`args`/`cwd` shape `.bob/mcp.json` declares)
and drives it purely over the real MCP stdio wire protocol using the `mcp`
SDK's own client — no in-process function calls. It proves a
`chaos_run_experiment` call followed by a `faultlens_get_context` call in
the same session returns the real run's data, not something fabricated for
the test.

**Surface 1 (in-app provider) is prepared but not connected.** There is no
real IBM Bob HTTP API, SDK, or credential wired into this repository. The
`BobAIProvider` class (`app/ai/providers/bob.py`) exists specifically so
this can be activated later without redesigning anything:

```python
class BobAIProvider(BaseAIProvider):
    ...
```

Selecting it via `AI_PROVIDER=bob` makes it the active provider, but every
call currently raises `AIProviderNotConfiguredError` (if `BOB_API_ENDPOINT`
/ `BOB_API_KEY` aren't set) or `NotImplementedError` (if they are, since
there's still no real HTTP call implemented). `AIAnalysisService` catches
both and returns an honest `AIInsight` with `status: "not_configured"` — the
experiment, its metrics, and its resilience analysis are entirely
unaffected; only the AI Insights panel shows the notice.

## What's required to activate a real in-app IBM Bob connection (Surface 1)

1. A real IBM Bob (or watsonx, or other) HTTP endpoint and API key. **None
   of this was found anywhere in this repository or environment** — this is
   configuration required but not available here, not something this
   codebase can supply on its own.
2. An HTTP client dependency (none is currently in `requirements.txt` for
   production use — `httpx` is currently dev-only, in
   `requirements-dev.txt`, for FastAPI's `TestClient`).
3. Implement `BobAIProvider.generate(prompt: str) -> str` to make the real
   call, replacing the `NotImplementedError`.
4. Set `AI_PROVIDER=bob` and the two env vars below in the backend's
   environment (`Backend/.env`, never committed — see
   `Backend/.env.example`).

`BOB_API_ENDPOINT` / `BOB_API_KEY` are **placeholder names chosen for this
stub**, not names taken from or verified against a real IBM Bob API
specification — no such specification was found in this repository or
environment to verify them against. Once a real spec exists, rename/replace
them to match it; don't treat their current names as a documented IBM Bob
contract.

No frontend changes, no API contract changes, and no changes to
`ExperimentRunData`/`AIInsight` are needed — the existing status model
already accounts for a real provider succeeding (`available`), being
unreachable (`unavailable`), or failing (`error`).

## What's required to fully activate the MCP (Surface 2) path

Nothing further, functionally — it already works, and is verified by a real
protocol-level test (see above). What's still open:

- The exact agent-side configuration needed to point a specific Bob client
  at `.bob/mcp.json` lives outside this repository (it's the calling
  agent's own setup) — FaultLens's code can't guarantee or verify that
  side of the connection, only that its own server correctly speaks MCP.
- `app/mcp/schemas.py` defines three Pydantic input schemas
  (`ChaosExperimentInput`, `AnalysisInput`, `NextExperimentInput`) that are
  never imported or used anywhere — dead code from earlier scaffolding, not
  wired into `app/mcp/server.py`'s actual tool signatures (which take plain
  `dict` parameters instead). Harmless, but worth knowing it isn't part of
  the real contract.

## The "IBM Bob" header indicator

FaultLens's UI shows a real, honestly-scoped MCP status in the header (see
`Frontend/src/components/layout/IBMBobMcpStatus.tsx`), polling
`GET /api/mcp/status` every 10 seconds. It never shows a live "Connected ●"
— MCP over stdio has no channel back to whatever process serves the REST
API, so a live socket-style status genuinely isn't observable here. Instead
it shows one of:

| State | Meaning |
|---|---|
| `MCP checking…` | Initial load, before the first poll resolves. |
| `MCP unavailable` | `app.mcp.server` failed to import in this backend, or the status request itself failed. |
| `Bob not connected` | The MCP server is available, but no MCP tool has ever been called against this database. |
| `MCP active` | A real MCP tool call was recorded within the last 2 minutes. |
| `MCP available` | The MCP server is available and has been used before, but not recently. |

`MCP active` and `MCP available` both show which tool was called and
how long ago — real data from `app/api/mcp_status.py`, not a guess.

## Demo: proving the connection live

`Backend/scripts/mcp_demo_client.py` is a real MCP client (not a mock) —
it spawns `app.mcp.server` exactly as `.bob/mcp.json` does and drives it
over the real stdio protocol using the `mcp` SDK's own client. To see the
header indicator update live:

```bash
# Terminal 1 — backend already running (see Getting Started in README.md)
# Terminal 2 — frontend already running, browser open on http://localhost:3000

# Terminal 3:
cd Backend
venv\Scripts\python.exe scripts\mcp_demo_client.py my-demo-system
```

Watch the header: "IBM BOB · Bob not connected" becomes
"IBM BOB · MCP active" within ~10 seconds (the poll interval) — genuine
evidence generated by an independent process talking real MCP, not a UI
toggle. `Frontend/e2e/mcp-integration.spec.ts` automates exactly this and
asserts on it.

## The mock provider is not IBM Bob

`MockAIProvider` (`app/ai/providers/mock.py`) is a deterministic, offline,
keyword-matching provider used for development and demos when no real
provider is configured. Every `AIInsight` it produces reports
`provider: "mock"` — the frontend never labels a mock response as if it came
from Bob, and this document exists partly so nobody else does either.

## Summary table

| | Status |
|---|---|
| MCP server exposing chaos/resilience/context tools | ✅ Working today — verified via a real stdio protocol round-trip test |
| Every MCP tool records real activity (`mcp_activity` table) | ✅ Working today |
| `chaos_run_experiment` persisting so results become real history | ✅ Working today |
| `GET /api/mcp/status` + header "IBM Bob" indicator | ✅ Working today — reflects real recorded activity, never a fabricated "Connected" |
| An external Bob agent calling FaultLens via MCP | ✅ The FaultLens side is verified; the agent-side config that would point a specific Bob client at `.bob/mcp.json` is outside this repo and unverifiable from here |
| `BobAIProvider` class, error/status handling, env var wiring | ✅ Prepared (explicitly labeled experimental/unofficial in its own messages) |
| Real HTTP call from `BobAIProvider` to an IBM Bob endpoint | ❌ Not implemented — no endpoint/SDK/credential exists here |
| `BOB_API_ENDPOINT` / `BOB_API_KEY` as an official IBM Bob contract | ❌ These are placeholder names chosen here, not verified against a real spec |
| `MockAIProvider` presented as IBM Bob anywhere in the UI | ❌ Never — always labeled `provider: "mock"` |

## Overall status (READY / PARTIAL / BLOCKED)

- **MCP integration (official): READY.** Server, tools, persistence,
  activity tracking, REST status endpoint, UI indicator, and a real
  protocol-level test all exist and pass today.
- **In-app Bob HTTP provider (experimental, unofficial): BLOCKED by
  environment.** No real IBM Bob endpoint, SDK, or credential exists in
  this repository or environment to connect to — this cannot be completed
  without configuration this codebase cannot supply on its own.
