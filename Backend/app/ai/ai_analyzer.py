from app.ai.prompt_builder import PromptBuilder
from app.ai.providers.base import BaseAIProvider
from app.models.ai_analysis import AIAnalysis
from app.models.resilience_analysis import ResilienceAnalysis


class AIAnalyzer:
    """
    Coordinates resilience analysis with an AI provider.
    """

    def __init__(
        self,
        provider: BaseAIProvider
    ):
        self.provider = provider
        self.prompt_builder = PromptBuilder()

    def analyze(
        self,
        resilience_analysis: ResilienceAnalysis
    ) -> AIAnalysis:
        """
        Generates an AI interpretation of the resilience analysis.
        """

        prompt = self.prompt_builder.build(
            resilience_analysis
        )

        response = self.provider.generate(prompt)

        return AIAnalysis(
            summary=response,
            root_cause=(
                "The observed risk is primarily associated with "
                "the affected dependency structure."
            ),
            risk_interpretation=(
                f"The deterministic resilience analysis classified "
                f"the system risk as "
                f"'{resilience_analysis.risk.level}'."
            ),
            recommendations=[
                recommendation.description
                for recommendation in resilience_analysis.recommendations
            ],
            confidence=0.85,
            provider=self.provider.name,
        )