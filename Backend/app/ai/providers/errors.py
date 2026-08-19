class AIProviderError(RuntimeError):
    """Base class for AI provider failures the service layer knows how to
    translate into an honest AIInsight status instead of a 500."""


class AIProviderNotConfiguredError(AIProviderError):
    """Raised when a provider is selected via AI_PROVIDER but is missing the
    configuration (endpoint, credentials) it needs to run at all."""


class AIProviderUnavailableError(AIProviderError):
    """Raised for transient failures reaching an otherwise-configured
    provider (timeout, connection error, rate limit)."""
