import logging

from fastapi import APIRouter, HTTPException

from app.models.ai_insight import AIInsight, AIInsightStatus
from app.models.experiment_api_response import ExperimentApiResponse
from app.models.experiment_request import ExperimentRequest
from app.models.experiment_response import ExperimentRunData
from app.models.next_experiment_suggestion import NextExperimentSuggestion
from app.models.resilience_analysis import ResilienceAnalysis
from app.models.scenario_comparison import ScenarioComparison, ScenarioComparisonRequest
from app.services.chaos_service import ChaosService
from app.services.resilience_analysis_service import (
    ResilienceAnalysisService,
)
from app.services.resilience_service import ResilienceService
from app.services.ai_analysis_service import AIAnalysisService
from app.services.persistence_service import PersistenceService
from app.services.resilience_orchestrator import (
    suggest_next_experiment as compute_next_experiment_suggestion,
)

logger = logging.getLogger(__name__)


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

    # AIAnalysisService already turns provider failures into an honest
    # AIInsight status instead of raising — this except is a last-resort
    # safety net so that even a bug in that translation can't take down an
    # otherwise-successful experiment result.
    try:
        ai_analysis = AIAnalysisService().analyze(
            analysis,
            experiment_type=request.experiment.type,
            target_node=request.experiment.target_node,
        )
    except Exception:
        logger.exception("AIAnalysisService raised unexpectedly")
        ai_analysis = AIInsight(
            status=AIInsightStatus.ERROR,
            provider="unknown",
            message="The AI provider failed to generate an analysis for this experiment.",
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


@router.post("/suggest-next", response_model=NextExperimentSuggestion)
def suggest_next_experiment(analysis: ResilienceAnalysis, last_target_node: str | None = None):
    """
    Suggests a logical follow-up experiment based on a completed resilience
    analysis (recovery failures and critical dependencies take priority).

    `last_target_node` (optional query param) is the node the experiment
    that produced this analysis already targeted. When supplied, it's used
    to avoid immediately re-suggesting the same node if the analysis offers
    a real alternative — see resilience_orchestrator.suggest_next_experiment.
    """
    suggestion = compute_next_experiment_suggestion(
        analysis.model_dump(mode="json"),
        last_target_node=last_target_node,
    )
    return NextExperimentSuggestion(**suggestion)


@router.post("/compare", response_model=ScenarioComparison)
def compare_experiments(request: ScenarioComparisonRequest):
    """
    Returns two to four previously-run experiment results for side-by-side comparison.
    """
    persistence = PersistenceService()
    runs: list[ExperimentRunData] = []

    for run_id in request.run_ids:
        result = persistence.get_experiment(run_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Experiment run '{run_id}' not found",
            )
        runs.append(result)

    return ScenarioComparison(runs=runs)
