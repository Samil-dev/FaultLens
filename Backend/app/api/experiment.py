from fastapi import APIRouter

from app.models.experiment_request import ExperimentRequest
from app.services.chaos_service import ChaosService

from app.models.experiment_response import ExperimentRunData
from app.models.experiment_api_response import ExperimentApiResponse
from app.services.resilience_service import ResilienceService

router = APIRouter(
    prefix="/api/experiments",
    tags=["Experiments"]
)

@router.post(
    "/run",
    response_model=ExperimentApiResponse
)
def run_experiment(request: ExperimentRequest):
    """
    Run a chaos experiment against a provided system.
    """

    run, events, comparisons = ChaosService().run_experiment(
        request.system,
        request.experiment
    )

    resilience_score = ResilienceService().calculate_score(
    comparisons,
    len(run.affected_nodes),
    len(request.system.nodes)
)

    return ExperimentApiResponse(
    success=True,
    data=ExperimentRunData(
        run=run,
        events=events,
        comparisons=comparisons,
        resilience_score=resilience_score
    ),
    error=None
    )