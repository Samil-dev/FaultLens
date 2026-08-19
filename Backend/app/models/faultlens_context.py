from typing import Optional

from pydantic import BaseModel, Field

from app.models.dependency import Dependency
from app.models.next_experiment_suggestion import NextExperimentSuggestion
from app.models.node import Node
from app.models.recovery import Recovery
from app.models.resilience_analysis import ResilienceAnalysis
from app.models.resilience_score import ResilienceScore


class HistoryEntrySummary(BaseModel):
    """One compact line of experiment history — enough for an AI provider
    (or Bob, via MCP) to reason about trends without re-sending full run
    payloads for every past experiment."""

    run_id: str
    target_node: str
    experiment_type: str
    resilience_score: float
    risk_level: str
    created_at: str


class FaultLensContext(BaseModel):
    """
    The structured evidence FaultLens hands to an AI provider (in-app) or to
    an external Bob agent (via MCP) so it can reason about the *whole*
    workflow instead of a single isolated result.

    Built entirely from real, already-persisted FaultLens data — nothing in
    this model is estimated or fabricated. Fields are None/empty when the
    corresponding stage hasn't happened yet (e.g. no experiment run yet), so
    a caller can distinguish "not applicable" from "zero".

    Reuses existing models (Node, Dependency, Recovery, ResilienceAnalysis,
    ResilienceScore, NextExperimentSuggestion) rather than duplicating their
    shapes.
    """

    # ── System / architecture ───────────────────────────────────────────────
    system_id: str
    system_name: str
    nodes: list[Node] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)

    # ── Target / experiment design ──────────────────────────────────────────
    target_node: Optional[str] = None
    experiment_type: Optional[str] = None
    duration_seconds: Optional[int] = None

    # ── Failure propagation (from the most recent run, if any) ─────────────
    run_id: Optional[str] = None
    run_status: Optional[str] = None
    affected_nodes: list[str] = Field(default_factory=list)
    propagation_path: list[str] = Field(default_factory=list)
    recoveries: list[Recovery] = Field(default_factory=list)

    # ── Resilience analysis (from the most recent run, if any) ─────────────
    resilience_score: Optional[ResilienceScore] = None
    analysis: Optional[ResilienceAnalysis] = None
    critical_nodes: list[str] = Field(default_factory=list)

    # ── History ──────────────────────────────────────────────────────────
    history: list[HistoryEntrySummary] = Field(default_factory=list)
    previous_recommendation: Optional[NextExperimentSuggestion] = None
