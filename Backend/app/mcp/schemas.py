from pydantic import BaseModel, Field

class ChaosExperimentInput(BaseModel):
    system: dict = Field(
        ...,
        description="System definition including nodes and dependencies"
    )

    experiment: dict = Field(
        ...,
        description="Chaos experiment definition"
    )

class AnalysisInput(BaseModel):
    system: dict = Field(
        ...,
        description="System definition"
    )

    experiment: dict = Field(
        ...,
        description="Experiment definition"
    )

class NextExperimentInput(BaseModel):
    analysis: dict = Field(
        ...,
        description="Complete resiliencie analysis"
    )