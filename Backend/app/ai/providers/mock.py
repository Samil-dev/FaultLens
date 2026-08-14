from app.ai.providers.base import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """
    Local provider used for development and integration testing.
    """

    @property
    def name(self) -> str:
        return "mock"

    def generate(
        self,
        prompt: str
    ) -> str:
        """
        Generates a deterministic development response.
        """

        return (
            "The system experienced meaningful degradation after "
            "the simulated failure. The dependency structure allowed "
            "the failure to propagate to downstream services."
        )