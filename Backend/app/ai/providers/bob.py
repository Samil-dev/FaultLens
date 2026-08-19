import os

from app.ai.providers.base import BaseAIProvider
from app.ai.providers.errors import AIProviderNotConfiguredError


class BobAIProvider(BaseAIProvider):
    """
    Prepared integration point for IBM Bob as an in-app AI provider.

    This is NOT a working connection to a real IBM Bob endpoint — no such
    endpoint, SDK, or credential exists in this repository or environment
    today. BOB_API_ENDPOINT / BOB_API_KEY below are placeholder variable
    names chosen for this stub, not names verified against any real IBM Bob
    API specification (none was found in this repo/environment to verify
    against) — treat them as "what a real HTTP-based provider would need",
    to be renamed/replaced once a real spec is available, not as a
    documented IBM Bob contract. Selecting "bob" via AI_PROVIDER makes this
    the active provider, but every call raises AIProviderNotConfiguredError
    until both are set, so AIAnalysisService reports an honest
    "not_configured" status instead of fabricating a response.

    See docs/ai-integration.md for exactly what's required to activate a
    real connection here (or to replace this with the real IBM Bob SDK).

    Note: today, FaultLens's actual working integration with Bob is the
    MCP server (app/mcp/server.py, registered via .bob/mcp.json) — an
    external Bob agent calls INTO FaultLens as a tool, rather than
    FaultLens calling OUT to a Bob API. This provider exists for the
    opposite direction (FaultLens calling a Bob-backed model as its
    in-app "AI Insights" provider), which is a separate, not-yet-available
    integration surface.
    """

    @property
    def name(self) -> str:
        return "bob"

    def __init__(self) -> None:
        self.endpoint = os.getenv("BOB_API_ENDPOINT", "").strip()
        self.api_key = os.getenv("BOB_API_KEY", "").strip()

    def generate(self, prompt: str) -> str:
        if not self.endpoint or not self.api_key:
            raise AIProviderNotConfiguredError(
                "This experimental in-app IBM Bob HTTP path (AI_PROVIDER=bob) "
                "is not configured — BOB_API_ENDPOINT and/or BOB_API_KEY are "
                "not set. Note: this is NOT FaultLens's official Bob "
                "integration; that is MCP (see the 'IBM Bob' indicator in the "
                "header, and docs/ai-integration.md)."
            )

        # No real IBM Bob HTTP API/SDK is integrated yet. Even with
        # credentials present, there is nothing real to call — raising here
        # (rather than fabricating a response) keeps this honest.
        raise NotImplementedError(
            "This experimental in-app IBM Bob HTTP path has credentials "
            "configured but no real IBM Bob API call is implemented yet — "
            "no such endpoint/SDK exists to call. FaultLens's official Bob "
            "integration is MCP, not this path. See docs/ai-integration.md."
        )
