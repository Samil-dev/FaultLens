from fastapi import APIRouter

from app.models.experiment_request import ExperimentRequest
from app.services.chaos_service import ChaosService

from app.models.experiment_response import ExperimentRunData
from app.models.experiment_api_response import ExperimentApiResponse

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

    run, events = ChaosService().run_experiment(
        request.system,
        request.experiment
    )

    return ExperimentApiResponse(
        succes=True,
        data=ExperimentRunData(
            run=run,
            events=events
        ),
        error=None
    )