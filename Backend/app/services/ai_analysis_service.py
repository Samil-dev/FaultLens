import os

from app.ai.ai_analyzer import AIAnalyzer
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.mock import MockAIProvider
from app.models.ai_analysis import AIAnalysis
from app.models.resilience_analysis import ResilienceAnalysis

# Registry of available AI providers, keyed by the AI_PROVIDER env var.
# To integrate a real LLM, implement BaseAIProvider in app/ai/providers/,
# register it here, and set AI_PROVIDER + its API key as environment
# variables — no frontend or API contract changes are needed, since
# AIAnalysis always exposes the same shape regardless of provider.
_PROVIDERS: dict[str, type[BaseAIProvider]] = {
    "mock": MockAIProvider,
}


class AIAnalysisService:
    """
    Service responsible for AI-assisted resilience interpretation.
    """

    def __init__(self):
        provider_name = os.getenv("AI_PROVIDER", "mock").strip().lower()
        provider_cls = _PROVIDERS.get(provider_name, MockAIProvider)
        self.analyzer = AIAnalyzer(
            provider=provider_cls()
        )

    def analyze(
        self,
        resilience_analysis: ResilienceAnalysis,
        experiment_type: str = "service_down",
        target_node: str | None = None,
    ) -> AIAnalysis:
        """
        Generates an AI interpretation of a resilience analysis.
        """

        return self.analyzer.analyze(
            resilience_analysis,
            experiment_type=experiment_type,
            target_node=target_node,
        )