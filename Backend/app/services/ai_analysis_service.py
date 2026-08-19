import logging
import os

from app.ai.ai_analyzer import AIAnalyzer
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.bob import BobAIProvider
from app.ai.providers.errors import AIProviderNotConfiguredError, AIProviderUnavailableError
from app.ai.providers.mock import MockAIProvider
from app.models.ai_insight import AIInsight, AIInsightStatus
from app.models.resilience_analysis import ResilienceAnalysis

logger = logging.getLogger(__name__)

# Registry of available AI providers, keyed by the AI_PROVIDER env var.
# To integrate a real LLM, implement BaseAIProvider in app/ai/providers/,
# register it here, and set AI_PROVIDER + its credentials as environment
# variables — no frontend or API contract changes are needed, since
# AIInsight always exposes the same shape regardless of provider or outcome.
_PROVIDERS: dict[str, type[BaseAIProvider]] = {
    "mock": MockAIProvider,
    "bob": BobAIProvider,
}


class AIAnalysisService:
    """
    Service responsible for AI-assisted resilience interpretation.

    Guarantees that a provider failure of any kind (missing configuration,
    transient unavailability, or an unexpected error) is turned into an
    honestly-labeled AIInsight rather than an exception — the chaos
    experiment, its metrics, and its resilience analysis must never be lost
    just because the AI layer couldn't produce a response.
    """

    def __init__(self):
        requested_name = os.getenv("AI_PROVIDER", "mock").strip().lower()
        self._provider_cls = _PROVIDERS.get(requested_name, MockAIProvider)
        # Falls back to "mock" in the AIInsight too when AI_PROVIDER names an
        # unregistered provider, so the reported provider always matches the
        # class that actually ran.
        self.provider_name = requested_name if requested_name in _PROVIDERS else "mock"

    def analyze(
        self,
        resilience_analysis: ResilienceAnalysis,
        experiment_type: str = "service_down",
        target_node: str | None = None,
    ) -> AIInsight:
        """
        Generates an AI interpretation of a resilience analysis, or an
        explicit non-available AIInsight if the provider can't produce one.
        """

        try:
            provider = self._provider_cls()
        except AIProviderNotConfiguredError as exc:
            return AIInsight(
                status=AIInsightStatus.NOT_CONFIGURED,
                provider=self.provider_name,
                message=str(exc),
            )
        except Exception as exc:  # defensive: provider construction must never crash the request
            logger.exception("AI provider %s failed to initialize", self.provider_name)
            return AIInsight(
                status=AIInsightStatus.ERROR,
                provider=self.provider_name,
                message=f"AI provider '{self.provider_name}' failed to initialize: {exc}",
            )

        analyzer = AIAnalyzer(provider=provider)

        try:
            analysis = analyzer.analyze(
                resilience_analysis,
                experiment_type=experiment_type,
                target_node=target_node,
            )
        except AIProviderNotConfiguredError as exc:
            return AIInsight(
                status=AIInsightStatus.NOT_CONFIGURED,
                provider=provider.name,
                message=str(exc),
            )
        except AIProviderUnavailableError as exc:
            return AIInsight(
                status=AIInsightStatus.UNAVAILABLE,
                provider=provider.name,
                message=str(exc),
            )
        except NotImplementedError as exc:
            return AIInsight(
                status=AIInsightStatus.NOT_CONFIGURED,
                provider=provider.name,
                message=str(exc),
            )
        except Exception as exc:  # noqa: BLE001 — any other provider failure must not break the experiment
            logger.exception("AI provider %s failed to generate an analysis", provider.name)
            return AIInsight(
                status=AIInsightStatus.ERROR,
                provider=provider.name,
                message="The AI provider failed to generate an analysis for this experiment.",
            )

        return AIInsight(
            status=AIInsightStatus.AVAILABLE,
            provider=provider.name,
            analysis=analysis,
        )