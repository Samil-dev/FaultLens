"""
Tests for app/mcp/tools.py — the functions backing FaultLens's MCP server
(app/mcp/server.py), which is how an external Bob agent consumes FaultLens
data (registered via .bob/mcp.json).

These call the plain Python functions directly rather than spinning up an
MCP transport — the transport is the `mcp` SDK's responsibility, not
FaultLens's; what FaultLens owns and must test is the data these tools
return.
"""

import os
import tempfile

import pytest

from app.mcp.tools import get_faultlens_context, run_chaos_experiment


@pytest.fixture
def isolated_persistence(monkeypatch):
    """Points PersistenceService at a fresh temp SQLite file for this test
    only, so it doesn't read/write the shared session-scoped test_client db."""
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
    tmp.close()
    monkeypatch.setenv("CODETWIN_DATABASE_PATH", tmp.name)
    yield tmp.name


class TestGetFaultLensContext:
    def test_unknown_system_returns_error_dict_not_exception(self, isolated_persistence):
        result = get_faultlens_context("does-not-exist")
        assert "error" in result
        assert "does-not-exist" in result["error"]

    def test_known_system_with_no_runs_returns_topology_only(self, isolated_persistence):
        from app.models.node import Node
        from app.models.system import System
        from app.services.persistence_service import PersistenceService

        system = System(
            id="sys-mcp-1", name="MCP Test System",
            nodes=[Node(id="a", name="A", node_type="service")],
            dependencies=[],
        )
        PersistenceService().save_system(system)

        result = get_faultlens_context("sys-mcp-1")
        assert result["system_id"] == "sys-mcp-1"
        assert result["system_name"] == "MCP Test System"
        assert len(result["nodes"]) == 1
        assert result["run_id"] is None
        assert result["history"] == []

    def test_known_system_with_a_run_includes_propagation_and_analysis(self, isolated_persistence):
        from app.services.resilience_orchestrator import run_chaos_experiment
        from app.services.persistence_service import PersistenceService
        from app.models.system import System
        from app.models.experiment_response import ExperimentRunData
        from app.models.ai_insight import AIInsight, AIInsightStatus

        system_dict = {
            "id": "sys-mcp-2", "name": "MCP Test System 2",
            "nodes": [
                {"id": "gw", "name": "Gateway", "node_type": "gateway"},
                {"id": "svc", "name": "Service", "node_type": "service"},
            ],
            "dependencies": [{"source": "gw", "target": "svc", "type": "depends_on"}],
        }
        experiment_dict = {
            "id": "exp-mcp-1", "system_id": "sys-mcp-2", "target_node": "gw",
            "type": "service_down", "duration_seconds": 30,
        }

        outcome = run_chaos_experiment(system=system_dict, experiment=experiment_dict)

        system = System(**system_dict)
        result_obj = ExperimentRunData(
            run=outcome["run"],
            events=outcome["events"],
            comparisons=outcome["comparisons"],
            resilience_score=outcome["resilience_score"],
            analysis=outcome["analysis"],
            ai_analysis=AIInsight(status=AIInsightStatus.NOT_CONFIGURED, provider="mock"),
        )

        persistence = PersistenceService()
        persistence.save_system(system)
        persistence.save_experiment("sys-mcp-2", result_obj)

        context = get_faultlens_context("sys-mcp-2")
        assert context["run_id"] == outcome["run"]["id"]
        assert context["propagation_path"][0] == "gw"
        assert context["analysis"]["risk"]["level"] in {"low", "moderate", "high", "critical"}
        # get_faultlens_context never passes an `experiment=` object to
        # build_context() — only `run=` — so duration_seconds must come
        # from SimulationRun.duration_seconds, not be silently null.
        assert context["duration_seconds"] == 30


class TestRunChaosExperimentPersists:
    """
    app.mcp.tools.run_chaos_experiment (the actual MCP tool implementation,
    distinct from the non-persisting resilience_orchestrator function of the
    same name) must persist automatically — this is what makes an experiment
    triggered by an external Bob agent via MCP become real, retrievable
    history instead of a one-off result Bob would have to remember itself.
    """

    def _payloads(self, system_id: str):
        system = {
            "id": system_id, "name": "MCP Auto-Persist System",
            "nodes": [
                {"id": "gw", "name": "Gateway", "node_type": "gateway"},
                {"id": "svc", "name": "Service", "node_type": "service"},
            ],
            "dependencies": [{"source": "gw", "target": "svc", "type": "depends_on"}],
        }
        experiment = {
            "id": f"exp-{system_id}", "system_id": system_id, "target_node": "gw",
            "type": "service_down", "duration_seconds": 30,
        }
        return system, experiment

    def test_experiment_run_via_mcp_is_immediately_visible_to_faultlens_get_context(
        self, isolated_persistence
    ):
        system_id = "sys-mcp-autopersist-1"
        system, experiment = self._payloads(system_id)

        outcome = run_chaos_experiment(system=system, experiment=experiment)
        assert outcome["run"]["status"] == "completed"

        # No manual PersistenceService calls here — if run_chaos_experiment
        # didn't persist, this would come back as a topology-only context
        # with run_id None.
        context = get_faultlens_context(system_id)
        assert context["run_id"] == outcome["run"]["id"]
        assert context["propagation_path"] == ["gw"]

    def test_result_includes_an_ai_insight(self, isolated_persistence):
        system, experiment = self._payloads("sys-mcp-autopersist-2")
        outcome = run_chaos_experiment(system=system, experiment=experiment)

        assert "ai_analysis" in outcome
        assert outcome["ai_analysis"]["status"] == "available"
        assert outcome["ai_analysis"]["provider"] == "mock"

    def test_second_run_appears_in_history_for_suggest_next(self, isolated_persistence):
        from app.mcp.tools import suggest_next_experiment

        system_id = "sys-mcp-autopersist-3"
        system, first_experiment = self._payloads(system_id)
        run_chaos_experiment(system=system, experiment=first_experiment)

        second_experiment = {
            "id": "exp-second", "system_id": system_id, "target_node": "svc",
            "type": "service_down", "duration_seconds": 30,
        }
        second_outcome = run_chaos_experiment(system=system, experiment=second_experiment)

        analysis = second_outcome["analysis"]
        suggestion = suggest_next_experiment(analysis=analysis, system_id=system_id)
        # Only assert the call succeeds and returns a well-formed suggestion —
        # the specific recommendation depends on this tiny fixture's
        # (deliberately trivial) resilience characteristics.
        assert "recommendation_type" in suggestion


class TestMcpActivityIsRecorded:
    """
    Every real MCP tool call must leave evidence in PersistenceService's
    mcp_activity table — this is what GET /api/mcp/status (and the
    frontend's "IBM Bob via MCP" indicator) reports, so it must reflect an
    MCP tool genuinely having been invoked, not a fabricated flag.
    """

    def test_run_chaos_experiment_records_activity(self, isolated_persistence):
        from app.services.persistence_service import PersistenceService

        system, experiment = TestRunChaosExperimentPersists()._payloads("sys-activity-1")
        run_chaos_experiment(system=system, experiment=experiment)

        activity = PersistenceService().get_last_mcp_activity()
        assert activity is not None
        assert activity["tool_name"] == "chaos_run_experiment"
        assert activity["system_id"] == "sys-activity-1"

    def test_get_faultlens_context_records_activity(self, isolated_persistence):
        from app.services.persistence_service import PersistenceService

        get_faultlens_context("sys-activity-2")

        activity = PersistenceService().get_last_mcp_activity()
        assert activity is not None
        assert activity["tool_name"] == "faultlens_get_context"
        assert activity["system_id"] == "sys-activity-2"

    def test_get_resilience_analysis_records_activity(self, isolated_persistence):
        from app.mcp.tools import get_resilience_analysis
        from app.services.persistence_service import PersistenceService

        system, experiment = TestRunChaosExperimentPersists()._payloads("sys-activity-3")
        get_resilience_analysis(system=system, experiment=experiment)

        activity = PersistenceService().get_last_mcp_activity()
        assert activity is not None
        assert activity["tool_name"] == "chaos_get_resilience_analysis"
        assert activity["system_id"] == "sys-activity-3"

    def test_suggest_next_experiment_records_activity(self, isolated_persistence):
        from app.mcp.tools import suggest_next_experiment
        from app.services.persistence_service import PersistenceService

        clean_analysis = {
            "impact": {"blast_radius": 0.0, "affected_nodes": 0, "total_nodes": 1, "critical_nodes": [], "average_metric_impact": 0.0},
            "recovery": {"recovered_nodes": 0, "total_recovery_nodes": 0, "average_recovery_seconds": 0.0, "max_recovery_seconds": 0.0, "failed_recoveries": []},
            "risk": {"level": "low", "reason": "No impact observed."},
            "recommendations": [],
        }
        suggest_next_experiment(analysis=clean_analysis, system_id="sys-activity-4")

        activity = PersistenceService().get_last_mcp_activity()
        assert activity is not None
        assert activity["tool_name"] == "chaos_suggest_next_experiment"
        assert activity["system_id"] == "sys-activity-4"
