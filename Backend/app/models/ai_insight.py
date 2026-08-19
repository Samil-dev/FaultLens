from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.models.ai_analysis import AIAnalysis


class AIInsightStatus(str, Enum):
    # A real analysis was produced by the configured provider.
    AVAILABLE = "available"
    # AI_PROVIDER points at a provider that requires configuration
    # (endpoint/credentials) that hasn't been supplied yet.
    NOT_CONFIGURED = "not_configured"
    # The provider is configured but could not be reached (timeout,
    # connection error, rate limit) — a transient condition.
    UNAVAILABLE = "unavailable"
    # The provider was reached/invoked but failed unexpectedly.
    ERROR = "error"


class AIInsight(BaseModel):
    """
    Wraps the AI-assisted interpretation of a resilience analysis with an
    explicit status, so a provider failure can never take the rest of an
    experiment result down with it.

    Only `status == AVAILABLE` carries a populated `analysis`. Every other
    status is a first-class, honestly-labeled outcome — the frontend must
    render each one distinctly and must never present `message` as if it
    were a real AI-generated response.
    """

    status: AIInsightStatus = Field(
        ...,
        description="Explicit outcome of attempting to generate an AI insight",
    )

    provider: str = Field(
        ...,
        description="Name of the AI provider that was attempted (e.g. 'mock', 'bob')",
    )

    analysis: Optional[AIAnalysis] = Field(
        default=None,
        description="The AI-generated analysis, present only when status is 'available'",
    )

    message: Optional[str] = Field(
        default=None,
        description="Human-readable explanation, present for any non-available status",
    )
