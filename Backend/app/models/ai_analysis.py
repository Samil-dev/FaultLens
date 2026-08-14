from pydantic import BaseModel, Field


class AIAnalysis(BaseModel):
    # Resumen general generado a partir del análisis de resiliencia.
    summary: str = Field(
        ...,
        description="AI-generated summary of the resilience analysis"
    )

    # Posible causa principal del problema.
    root_cause: str = Field(
        ...,
        description="Interpretation of the most likely root cause"
    )

    # Interpretación del nivel de riesgo.
    risk_interpretation: str = Field(
        ...,
        description="Interpretation of the observed risk"
    )

    # Recomendaciones explicadas por la IA.
    recommendations: list[str] = Field(
        default_factory=list,
        description="AI-generated recommendations"
    )

    # Nivel de confianza de la interpretación.
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence of the AI analysis"
    )

    # Identifica qué proveedor generó la respuesta.
    provider: str = Field(
        ...,
        description="AI provider used for the analysis"
    )