from pydantic import BaseModel, Field

from app.models.experiment_response import ExperimentRunData


class ScenarioComparisonRequest(BaseModel):
    run_ids: list[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="Two to four experiment run IDs to compare side-by-side",
    )


class ScenarioComparison(BaseModel):
    runs: list[ExperimentRunData] = Field(
        ...,
        description="Ordered list of experiment run results for comparison",
    )
