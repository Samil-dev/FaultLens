from pydantic import BaseModel, Field

from app.models.impact_analysis import ImpactAnalysis
from app.models.recovery_analysis import RecoveryAnalysis
from app.models.risk_analysis import RiskAnalysis
from app.models.recommendation import Recommendation


class ResilienceAnalysis(BaseModel):
    # Análisis del impacto.
    impact: ImpactAnalysis = Field(
        ...,
        description="Impact analysis"
    )

    # Análisis de recuperación.
    recovery: RecoveryAnalysis = Field(
        ...,
        description="Recovery analysis"
    )

    # Evaluación del riesgo.
    risk: RiskAnalysis = Field(
        ...,
        description="Risk analysis"
    )

    # Recomendaciones generadas por el sistema.
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Resilience recommendations"
    )