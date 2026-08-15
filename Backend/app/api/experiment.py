from fastapi import APIRouter

from app.models.experiment_api_response import ExperimentApiResponse
from app.models.experiment_request import ExperimentRequest
from app.models.experiment_response import ExperimentRunData
from app.services.chaos_service import ChaosService
from app.services.resilience_analysis_service import (
    ResilienceAnalysisService,
)
from app.services.resilience_service import ResilienceService
from app.services.ai_analysis_service import AIAnalysisService
from app.services.persistence_service import PersistenceService


router = APIRouter(
    prefix="/api/experiments",
    tags=["Experiments"],
)


@router.post(
    "/run",
    response_model=ExperimentApiResponse,
)
def run_experiment(request: ExperimentRequest):
    """
    Runs a chaos experiment against a provided system.
    """

    # Execute the chaos experiment.
    run, events, comparisons = ChaosService().run_experiment(
        request.system,
        request.experiment,
    )

    # Calculate the deterministic resilience score.
    resilience_score = ResilienceService().calculate_score(
        comparisons,
        len(run.affected_nodes),
        len(request.system.nodes),
    )

    # Generate the complete resilience analysis.
    analysis = ResilienceAnalysisService().analyze(
        experiment=request.experiment,
        run=run,
        comparisons=comparisons,
        score=resilience_score,
        total_nodes=len(request.system.nodes),
    )

    ai_analysis = AIAnalysisService().analyze(
        analysis,
        experiment_type=request.experiment.type,
    )

    result = ExperimentRunData(
        run=run,
        events=events,
        comparisons=comparisons,
        resilience_score=resilience_score,
        analysis=analysis,
        ai_analysis=ai_analysis,
    )
    PersistenceService().save_system(request.system)
    PersistenceService().save_experiment(request.system.id, result)

    return ExperimentApiResponse(
        success=True,
        data=result,
        error=None,
    )


@router.get("/", response_model=list[ExperimentRunData])
def list_experiments(system_id: str | None = None):
    return PersistenceService().list_experiments(system_id)
