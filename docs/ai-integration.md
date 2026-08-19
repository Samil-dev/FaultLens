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

## What's required to activate a real in-app IBM Bob connection

1. A real IBM Bob (or watsonx, or other) HTTP endpoint and API key.
2. An HTTP client dependency (none is currently in `requirements.txt` for
   production use — `httpx` is currently dev-only, in
   `requirements-dev.txt`, for FastAPI's `TestClient`).
3. Implement `BobAIProvider.generate(prompt: str) -> str` to make the real
   call, replacing the `NotImplementedError`.
4. Set `AI_PROVIDER=bob`, `BOB_API_ENDPOINT`, and `BOB_API_KEY` in the
   backend's environment (`Backend/.env`, never committed — see
   `Backend/.env.example`).

No frontend changes, no API contract changes, and no changes to
`ExperimentRunData`/`AIInsight` are needed — the existing status model
already accounts for a real provider succeeding (`available`), being
unreachable (`unavailable`), or failing (`error`).

## What's required to fully activate the MCP (Surface 1) path

Nothing further, functionally — it already works. What's still missing is
declaring the `mcp` package's version in a way that matches how the rest of
the team installs dependencies, and documenting the exact agent-side
configuration needed to point a specific Bob client at `.bob/mcp.json` — that
configuration lives outside this repository (it's the calling agent's
setup), so it isn't something FaultLens's own code can guarantee.

## The mock provider is not IBM Bob

`MockAIProvider` (`app/ai/providers/mock.py`) is a deterministic, offline,
keyword-matching provider used for development and demos when no real
provider is configured. Every `AIInsight` it produces reports
`provider: "mock"` — the frontend never labels a mock response as if it came
from Bob, and this document exists partly so nobody else does either.

## Summary table

| | Status |
|---|---|
| MCP server exposing chaos/resilience/context tools | ✅ Working today |
| An external Bob agent calling FaultLens via MCP | ✅ Working today (agent-side config not included in this repo) |
| `BobAIProvider` class, error/status handling, env var wiring | ✅ Prepared |
| Real HTTP call from `BobAIProvider` to an IBM Bob endpoint | ❌ Not implemented — no endpoint/SDK/credential exists here |
| `MockAIProvider` presented as IBM Bob anywhere in the UI | ❌ Never — always labeled `provider: "mock"` |
