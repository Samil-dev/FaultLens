from app.ai.providers.base import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """
    Local provider used for development and integration testing.

    Returns a deterministic response that varies by experiment type,
    detected via keywords present in the structured prompt.
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

        The response is tailored to the experiment type by inspecting
        keywords in the prompt produced by PromptBuilder.
        """

        prompt_lower = prompt.lower()

        if "latency_spike" in prompt_lower or "latency spike" in prompt_lower:
            return (
                "High latency was injected into the target node, causing response "
                "times to spike significantly. The elevated latency propagated to "
                "downstream services via synchronous dependency chains, increasing "
                "end-to-end request times across the system. The dependency "
                "structure amplified the latency effect beyond the injection point."
            )

        if (
            "resource_exhaustion" in prompt_lower
            or "resource exhaustion" in prompt_lower
        ):
            return (
                "CPU and memory resources on the target node were saturated, "
                "causing the node to become heavily loaded and slow to respond. "
                "Resource pressure propagated to dependent services, which "
                "experienced elevated error rates and reduced throughput. "
                "The system's ability to recover was constrained by the "
                "sustained resource contention on the target node."
            )

        # Default: service_down (or any unrecognised type)
        return (
            "The system experienced meaningful degradation after "
            "the simulated failure. The dependency structure allowed "
            "the failure to propagate to downstream services."
        )
