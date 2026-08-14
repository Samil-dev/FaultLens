from app.ai.ai_analyzer import AIAnalyzer
from app.ai.providers.mock import MockAIProvider
from app.models.ai_analysis import AIAnalysis
from app.models.resilience_analysis import ResilienceAnalysis


class AIAnalysisService:
    """
    Service responsible for AI-assisted resilience interpretation.
    """

    def __init__(self):
        self.analyzer = AIAnalyzer(
            provider=MockAIProvider()
        )

    def analyze(
        self,
        resilience_analysis: ResilienceAnalysis
    ) -> AIAnalysis:
        """
        Generates an AI interpretation of a resilience analysis.
        """

        return self.analyzer.analyze(
            resilience_analysis
        )