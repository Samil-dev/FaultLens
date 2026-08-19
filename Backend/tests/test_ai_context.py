"""
Tests for the FaultLens AI Context Pipeline: app/ai/context_builder.py and
its wiring into PromptBuilder.

These are unit tests against real model objects (no HTTP layer) — they
confirm the context assembled for an AI provider is built entirely from
real System/SimulationRun/ResilienceAnalysis data, and that PromptBuilder
actually includes it in the generated prompt text.
"""

from datetime import datetime, timezone

from app.ai.context_builder import build_context
from app.ai.prompt_builder import PromptBuilder
from app.models.dependency import Dependency
from app.models.experiment import Experiment
from app.models.impact_analysis import ImpactAnalysis
from app.models.node import Node
from app.models.recovery_analysis import RecoveryAnalysis
from app.models.resilience_analysis import ResilienceAnalysis
from app.models.resilience_score import ResilienceScore
from app.models.risk_analysis import RiskAnalysis
from app.models.simulation_run import SimulationRun
from app.models.system import System


def _system() -> System:
    return System(
        id="sys-ctx",
        name="Context Test System",
        nodes=[
            Node(id="gw", name="Gateway", node_type="gateway"),
            Node(id="svc", name="Service", node_type="service"),
        ],
        dependencies=[Dependency(source="gw", target="svc")],
    )


def _analysis() -> ResilienceAnalysis:
    return ResilienceAnalysis(
        impact=ImpactAnalysis(
            blast_radius=0.5,
            affected_nodes=1,
            total_nodes=2,
            critical_nodes=["svc"],
            average_metric_impact=0.4,
        ),
        recovery=RecoveryAnalysis(
            recovered_nodes=1,
            total_recovery_nodes=1,
            average_recovery_seconds=5.0,
            max_recovery_seconds=5.0,
            failed_recoveries=[],
        ),
        risk=RiskAnalysis(level="moderate", reason="Test reason."),
        recommendations=[],
    )


def _run() -> SimulationRun:
    return SimulationRun(
        id="run-ctx-1",
        experiment_id="exp-ctx-1",
        type="service_down",
        target_node="gw",
        status="completed",
        affected_nodes=["svc"],
        recoveries=[],
    )


class TestBuildContext:
    def test_system_topology_is_included_verbatim(self):
        system = _system()
        context = build_context(system=system)

        assert context.system_id == "sys-ctx"
        assert context.system_name == "Context Test System"
        assert [n.id for n in context.nodes] == ["gw", "svc"]
        assert len(context.dependencies) == 1

    def test_experiment_fields_populate_target_and_type(self):
        system = _system()
        experiment = Experiment(
            id="exp-ctx-1", system_id=system.id, target_node="gw",
            type="service_down", duration_seconds=30,
        )
        context = build_context(system=system, experiment=experiment)

        assert context.target_node == "gw"
        assert context.experiment_type == "service_down"
        assert context.duration_seconds == 30

    def test_run_populates_propagation_path_from_real_data(self):
        system = _system()
        run = _run()
        context = build_context(system=system, run=run)

        assert context.run_id == "run-ctx-1"
        assert context.run_status == "completed"
        assert context.affected_nodes == ["svc"]
        # Propagation path is origin followed by affected nodes, in order —
        # not fabricated, derived directly from SimulationRun.
        assert context.propagation_path == ["gw", "svc"]

    def test_analysis_populates_critical_nodes(self):
        system = _system()
        context = build_context(system=system, analysis=_analysis())

        assert context.critical_nodes == ["svc"]
        assert context.analysis.risk.level == "moderate"

    def test_no_history_produces_empty_list_not_fabricated_entries(self):
        context = build_context(system=_system(), history=[])
        assert context.history == []

    def test_context_never_leaks_credentials_or_unrelated_fields(self):
        """The context model has no field for API keys, env vars, or
        anything beyond the workflow data it's documented to carry."""
        context = build_context(system=_system())
        dumped = context.model_dump()
        assert "api_key" not in dumped
        assert "credentials" not in dumped
        assert "secret" not in str(dumped).lower()


class TestPromptBuilderContextIntegration:
    def test_prompt_without_context_omits_context_section(self):
        prompt = PromptBuilder().build(_analysis(), experiment_type="service_down", target_node="gw")
        assert "Recent experiment history" not in prompt
        assert "Propagation path" not in prompt

    def test_prompt_with_context_includes_system_name_and_propagation(self):
        system = _system()
        context = build_context(system=system, run=_run(), analysis=_analysis())

        prompt = PromptBuilder().build(
            _analysis(), experiment_type="service_down", target_node="gw", context=context,
        )

        assert "Context Test System" in prompt
        assert "gw -> svc" in prompt
        assert "Recent experiment history" in prompt

    def test_prompt_with_context_reflects_real_history_not_placeholder_text(self):
        system = _system()
        past_run = SimulationRun(
            id="run-past-1", experiment_id="exp-past-1", type="latency_spike",
            target_node="svc", status="completed", affected_nodes=[],
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        from app.models.ai_insight import AIInsight, AIInsightStatus
        from app.models.experiment_response import ExperimentRunData

        past_result = ExperimentRunData(
            run=past_run,
            resilience_score=ResilienceScore(score=72.0, rating="good", affected_nodes=0, total_nodes=2),
            analysis=_analysis(),
            ai_analysis=AIInsight(status=AIInsightStatus.NOT_CONFIGURED, provider="mock"),
        )

        context = build_context(system=system, history=[past_result])
        prompt = PromptBuilder().build(_analysis(), context=context)

        assert "latency_spike" in prompt
        assert "svc" in prompt
        assert "72.0" in prompt
