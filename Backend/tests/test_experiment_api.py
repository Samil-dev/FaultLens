"""
Integration tests for the FastAPI experiment, system, and health endpoints.

Uses FastAPI's TestClient (backed by starlette.testclient) which runs the
full ASGI stack synchronously — no running server required.

The test_client fixture (defined in conftest.py) redirects SQLite to a
temp file so these tests never touch the real codetwin.sqlite3.

Endpoints under test:
  GET  /api/health
  POST /api/systems/
  GET  /api/systems/
  POST /api/experiments/run
  GET  /api/experiments/
"""

import pytest


# ── Health ─────────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_returns_200(self, test_client):
        response = test_client.get("/api/health")
        assert response.status_code == 200

    def test_body_has_success_true(self, test_client):
        body = test_client.get("/api/health").json()
        assert body["success"] is True

    def test_body_has_status_healthy(self, test_client):
        body = test_client.get("/api/health").json()
        assert body["data"]["status"] == "healthy"


# ── System endpoints ──────────────────────────────────────────────────────────

class TestSystemEndpoints:
    def test_create_system_returns_200(self, test_client, demo_system):
        payload = demo_system.model_dump(mode="json")
        response = test_client.post("/api/systems/", json=payload)
        assert response.status_code == 200

    def test_create_system_returns_success_true(self, test_client, demo_system):
        payload = demo_system.model_dump(mode="json")
        body = test_client.post("/api/systems/", json=payload).json()
        assert body["success"] is True

    def test_create_system_echoes_system_id(self, test_client, demo_system):
        payload = demo_system.model_dump(mode="json")
        body = test_client.post("/api/systems/", json=payload).json()
        assert body["data"]["id"] == demo_system.id

    def test_list_systems_returns_200(self, test_client):
        response = test_client.get("/api/systems/")
        assert response.status_code == 200

    def test_list_systems_returns_list(self, test_client):
        body = test_client.get("/api/systems/").json()
        assert isinstance(body, list)

    def test_create_system_with_duplicate_node_ids_returns_422(self, test_client, demo_system):
        payload = demo_system.model_dump(mode="json")
        # Duplicate one node id
        payload["nodes"].append(payload["nodes"][0].copy())
        response = test_client.post("/api/systems/", json=payload)
        assert response.status_code == 422


# ── Experiment run endpoint ───────────────────────────────────────────────────

class TestRunExperimentEndpoint:
    def test_service_down_returns_200(
        self, test_client, run_experiment_payload_db_main
    ):
        response = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        )
        assert response.status_code == 200

    def test_service_down_response_success_true(
        self, test_client, run_experiment_payload_db_main
    ):
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        ).json()
        assert body["success"] is True

    def test_service_down_response_has_run(
        self, test_client, run_experiment_payload_db_main
    ):
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        ).json()
        assert "run" in body["data"]
        assert body["data"]["run"]["status"] == "completed"
        assert body["data"]["run"]["type"] == "service_down"
        assert body["data"]["run"]["target_node"] == "db-main"

    def test_service_down_response_has_resilience_score(
        self, test_client, run_experiment_payload_db_main
    ):
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        ).json()
        score = body["data"]["resilience_score"]
        assert "score" in score
        assert "rating" in score
        assert isinstance(score["score"], float)

    def test_service_down_response_has_analysis(
        self, test_client, run_experiment_payload_db_main
    ):
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        ).json()
        analysis = body["data"]["analysis"]
        assert "impact"          in analysis
        assert "recovery"        in analysis
        assert "risk"            in analysis
        assert "recommendations" in analysis

    def test_service_down_response_has_ai_analysis(
        self, test_client, run_experiment_payload_db_main
    ):
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        ).json()
        insight = body["data"]["ai_analysis"]
        assert insight["status"]   == "available"
        assert insight["provider"] == "mock"
        assert insight["message"] is None

        ai = insight["analysis"]
        assert "summary"            in ai
        assert "root_cause"         in ai
        assert "risk_interpretation" in ai
        assert "recommendations"    in ai
        assert "provider"           in ai
        assert ai["provider"] == "mock"

    def test_service_down_response_has_events(
        self, test_client, run_experiment_payload_db_main
    ):
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        ).json()
        events = body["data"]["events"]
        assert isinstance(events, list)
        assert len(events) > 0

    def test_service_down_first_event_is_failure_injected(
        self, test_client, run_experiment_payload_db_main
    ):
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        ).json()
        assert body["data"]["events"][0]["event_type"] == "failure_injected"
        assert body["data"]["events"][0]["node_id"] == "db-main"

    def test_service_down_response_has_comparisons(
        self, test_client, run_experiment_payload_db_main
    ):
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        ).json()
        comps = body["data"]["comparisons"]
        assert isinstance(comps, list)
        # One comparison per node in the system
        assert len(comps) == 10

    def test_service_down_comparisons_have_required_fields(
        self, test_client, run_experiment_payload_db_main
    ):
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        ).json()
        for comp in body["data"]["comparisons"]:
            assert "node_id"            in comp
            assert "cpu_usage_delta"    in comp
            assert "memory_usage_delta" in comp
            assert "latency_delta_ms"   in comp
            assert "error_rate_delta"   in comp

    def test_gateway_service_down_has_zero_affected_nodes(
        self, test_client, run_experiment_payload_gateway
    ):
        """gateway has no dependents, so affected_nodes must be empty."""
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_gateway
        ).json()
        assert body["data"]["run"]["affected_nodes"] == []

    def test_db_main_service_down_affected_nodes_count(
        self, test_client, run_experiment_payload_db_main
    ):
        """
        db-main failure propagates to 4 unique affected nodes after the
        DependencyGraph deduplication fix (Phase 2A):
        auth, catalog, orders, gateway — each exactly once.
        """
        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        ).json()
        affected = body["data"]["run"]["affected_nodes"]
        assert len(affected) == 4
        assert len(affected) == len(set(affected))

    def test_unknown_experiment_type_returns_422(self, test_client, demo_system):
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": "exp-bad",
                "system_id": demo_system.id,
                "target_node": "gateway",
                "type": "nuclear_option",
                "duration_seconds": 10,
            },
        }
        response = test_client.post("/api/experiments/run", json=payload)
        assert response.status_code == 422

    def test_unknown_target_node_returns_400(self, test_client, demo_system):
        """
        An unknown target_node passes Pydantic validation (it's just a string)
        but the ChaosEngine raises ValueError. The ValueError exception handler
        in main.py catches it and returns HTTP 400.
        """
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": "exp-bad-node",
                "system_id": demo_system.id,
                "target_node": "nonexistent-node",
                "type": "service_down",
                "duration_seconds": 10,
            },
        }
        response = test_client.post("/api/experiments/run", json=payload)
        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"

    def test_system_id_mismatch_returns_400(self, test_client, demo_system):
        """
        experiment.system_id != system.id → ChaosEngine raises ValueError.
        The ValueError exception handler returns HTTP 400.
        """
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": "exp-mismatch",
                "system_id": "different-system",
                "target_node": "gateway",
                "type": "service_down",
                "duration_seconds": 10,
            },
        }
        response = test_client.post("/api/experiments/run", json=payload)
        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"

    def test_traffic_spike_returns_200(self, test_client, demo_system):
        """traffic_spike is now fully implemented and must return 200."""
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": "exp-traffic",
                "system_id": demo_system.id,
                "target_node": "gateway",
                "type": "traffic_spike",
                "duration_seconds": 10,
            },
        }
        response = test_client.post("/api/experiments/run", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True

    def test_latency_spike_returns_200(self, test_client, demo_system):
        """latency_spike is a supported experiment type and must return 200."""
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": "exp-latency-http",
                "system_id": demo_system.id,
                "target_node": "db-main",
                "type": "latency_spike",
                "duration_seconds": 30,
            },
        }
        response = test_client.post("/api/experiments/run", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_resource_exhaustion_returns_200(self, test_client, demo_system):
        """resource_exhaustion is a supported experiment type and must return 200."""
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": "exp-resource-http",
                "system_id": demo_system.id,
                "target_node": "db-main",
                "type": "resource_exhaustion",
                "duration_seconds": 30,
            },
        }
        response = test_client.post("/api/experiments/run", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_latency_spike_response_has_correct_shape(self, test_client, demo_system):
        """latency_spike response must include all top-level fields."""
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": "exp-latency-shape",
                "system_id": demo_system.id,
                "target_node": "auth",
                "type": "latency_spike",
                "duration_seconds": 30,
            },
        }
        body = test_client.post("/api/experiments/run", json=payload).json()
        data = body["data"]
        assert "run"              in data
        assert "events"           in data
        assert "comparisons"      in data
        assert "resilience_score" in data
        assert "analysis"         in data
        assert "ai_analysis"      in data
        # Target node event must be node_degraded (not failure_injected).
        first_event = data["events"][0]
        assert first_event["event_type"] == "node_degraded"
        assert first_event["node_id"] == "auth"
        # run.target_node/type let clients identify the target without
        # relying on the failure_injected event, which only service_down emits.
        assert data["run"]["target_node"] == "auth"
        assert data["run"]["type"] == "latency_spike"


    def test_traffic_spike_response_has_correct_shape(self, test_client, demo_system):
        """traffic_spike response must include all top-level fields."""
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": "exp-traffic-shape",
                "system_id": demo_system.id,
                "target_node": "db-main",
                "type": "traffic_spike",
                "duration_seconds": 30,
            },
        }
        body = test_client.post("/api/experiments/run", json=payload).json()
        data = body["data"]
        assert "run"              in data
        assert "events"           in data
        assert "comparisons"      in data
        assert "resilience_score" in data
        assert "analysis"         in data
        assert "ai_analysis"      in data
        # Target node event must be node_degraded (not failure_injected).
        first_event = data["events"][0]
        assert first_event["event_type"] == "node_degraded"
        assert first_event["node_id"] == "db-main"
        assert data["run"]["target_node"] == "db-main"
        assert data["run"]["type"] == "traffic_spike"

    def test_traffic_spike_ai_analysis_has_traffic_specific_summary(
        self, test_client, demo_system
    ):
        """The mock AI provider must detect traffic_spike and return tailored text."""
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": "exp-traffic-ai",
                "system_id": demo_system.id,
                "target_node": "auth",
                "type": "traffic_spike",
                "duration_seconds": 30,
            },
        }
        body = test_client.post("/api/experiments/run", json=payload).json()
        summary = body["data"]["ai_analysis"]["analysis"]["summary"].lower()
        assert "traffic" in summary or "request" in summary or "overload" in summary

    def test_traffic_spike_ai_root_cause_contains_target_node(
        self, test_client, demo_system
    ):
        """The AI root_cause must reference the target node and traffic_spike."""
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": "exp-traffic-root-cause",
                "system_id": demo_system.id,
                "target_node": "auth",
                "type": "traffic_spike",
                "duration_seconds": 30,
            },
        }
        body = test_client.post("/api/experiments/run", json=payload).json()
        root_cause = body["data"]["ai_analysis"]["analysis"]["root_cause"].lower()
        # Evidence-based root cause must mention the target node
        assert "auth" in root_cause


# ── AI provider failure isolation ─────────────────────────────────────────────
# A provider that can't produce an analysis (missing config, or an outright
# failure) must never take the rest of the experiment result down with it.

class TestAIProviderFailureIsolation:
    def test_unconfigured_bob_provider_reports_not_configured(
        self, test_client, run_experiment_payload_db_main, monkeypatch
    ):
        monkeypatch.setenv("AI_PROVIDER", "bob")
        monkeypatch.delenv("BOB_API_ENDPOINT", raising=False)
        monkeypatch.delenv("BOB_API_KEY", raising=False)

        response = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        )
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True

        insight = body["data"]["ai_analysis"]
        assert insight["status"] == "not_configured"
        assert insight["provider"] == "bob"
        assert insight["analysis"] is None
        assert insight["message"]  # a human-readable explanation is present

        # The rest of the experiment result is completely unaffected.
        assert body["data"]["run"]["status"] == "completed"
        assert "analysis" in body["data"]
        assert "resilience_score" in body["data"]
        assert "comparisons" in body["data"]

    def test_provider_that_raises_reports_error_without_losing_the_experiment(
        self, test_client, run_experiment_payload_db_main, monkeypatch
    ):
        import app.services.ai_analysis_service as ai_service_module
        from app.ai.providers.base import BaseAIProvider

        class ExplodingProvider(BaseAIProvider):
            @property
            def name(self) -> str:
                return "exploding"

            def generate(self, prompt: str) -> str:
                raise RuntimeError("simulated provider outage")

        monkeypatch.setitem(ai_service_module._PROVIDERS, "exploding", ExplodingProvider)
        monkeypatch.setenv("AI_PROVIDER", "exploding")

        response = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        )
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True

        insight = body["data"]["ai_analysis"]
        assert insight["status"] == "error"
        assert insight["provider"] == "exploding"
        assert insight["analysis"] is None
        assert insight["message"]

        # The experiment itself, its metrics, and its resilience analysis
        # must all still be present and correct.
        assert body["data"]["run"]["status"] == "completed"
        assert body["data"]["analysis"]["risk"]["level"] in {"low", "moderate", "high", "critical"}
        assert body["data"]["resilience_score"]["score"] >= 0

    def test_default_mock_provider_is_unaffected_by_the_registry(
        self, test_client, run_experiment_payload_gateway, monkeypatch
    ):
        """Sanity check: AI_PROVIDER unset still resolves to the working mock
        provider, unaffected by whatever the previous two tests registered."""
        monkeypatch.delenv("AI_PROVIDER", raising=False)

        body = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_gateway
        ).json()
        insight = body["data"]["ai_analysis"]
        assert insight["status"] == "available"
        assert insight["provider"] == "mock"
        assert insight["analysis"]["summary"]


# ── Experiment history endpoint ───────────────────────────────────────────────

class TestListExperimentsEndpoint:
    def test_list_experiments_returns_200(self, test_client):
        response = test_client.get("/api/experiments/")
        assert response.status_code == 200

    def test_list_experiments_returns_list(self, test_client):
        body = test_client.get("/api/experiments/").json()
        assert isinstance(body, list)


# ── Suggest next experiment endpoint ──────────────────────────────────────────

class TestSuggestNextExperimentEndpoint:
    def test_returns_200_and_valid_shape(self, test_client, run_experiment_payload_db_main):
        run_resp = test_client.post("/api/experiments/run", json=run_experiment_payload_db_main).json()
        analysis = run_resp["data"]["analysis"]

        response = test_client.post("/api/experiments/suggest-next", json=analysis)
        assert response.status_code == 200

        body = response.json()
        assert body["recommendation_type"] in {
            "recovery_validation",
            "critical_dependency",
            "high_risk_follow_up",
            "no_immediate_follow_up",
        }
        assert "reason" in body
        assert "risk_level" in body

    def test_critical_dependency_suggests_service_down_on_a_critical_node(
        self, test_client, run_experiment_payload_db_main
    ):
        run_resp = test_client.post("/api/experiments/run", json=run_experiment_payload_db_main).json()
        analysis = run_resp["data"]["analysis"]
        assert analysis["impact"]["critical_nodes"], "fixture must produce at least one critical node"

        body = test_client.post("/api/experiments/suggest-next", json=analysis).json()
        assert body["recommendation_type"] == "critical_dependency"
        assert body["suggested_experiment"]["type"] == "service_down"
        assert body["suggested_experiment"]["target_node"] in analysis["impact"]["critical_nodes"]

    def test_no_follow_up_when_analysis_is_clean(self, test_client):
        """A hand-built, low-impact analysis with no critical nodes or failed
        recoveries should not suggest a follow-up experiment."""
        clean_analysis = {
            "impact": {
                "blast_radius": 0.0,
                "affected_nodes": 0,
                "total_nodes": 10,
                "critical_nodes": [],
                "average_metric_impact": 0.0,
            },
            "recovery": {
                "recovered_nodes": 0,
                "total_recovery_nodes": 0,
                "average_recovery_seconds": 0.0,
                "max_recovery_seconds": 0.0,
                "failed_recoveries": [],
            },
            "risk": {"level": "low", "reason": "No impact observed."},
            "recommendations": [],
        }
        body = test_client.post("/api/experiments/suggest-next", json=clean_analysis).json()
        assert body["recommendation_type"] == "no_immediate_follow_up"
        assert body["suggested_experiment"] is None

    def test_malformed_body_returns_422(self, test_client):
        response = test_client.post("/api/experiments/suggest-next", json={"not": "an analysis"})
        assert response.status_code == 422

    def test_last_target_node_is_skipped_when_a_real_alternative_exists(self, test_client):
        """When critical_nodes has more than one entry, the node the user
        just tested (last_target_node) must not be re-suggested if another
        critical node is available."""
        analysis = {
            "impact": {
                "blast_radius": 0.4, "affected_nodes": 2, "total_nodes": 10,
                "critical_nodes": ["db-main", "orders"], "average_metric_impact": 0.6,
            },
            "recovery": {
                "recovered_nodes": 2, "total_recovery_nodes": 2,
                "average_recovery_seconds": 10.0, "max_recovery_seconds": 15.0,
                "failed_recoveries": [],
            },
            "risk": {"level": "moderate", "reason": "Notable impact observed."},
            "recommendations": [],
        }
        body = test_client.post(
            "/api/experiments/suggest-next?last_target_node=db-main", json=analysis
        ).json()
        assert body["recommendation_type"] == "critical_dependency"
        assert body["suggested_experiment"]["target_node"] == "orders"
        assert "orders" in body["reason"]

    def test_last_target_node_falls_back_to_itself_when_no_alternative(self, test_client):
        """When the only critical node IS the one just tested, it's still
        suggested (re-validation is legitimate) but the reason must say so
        honestly instead of implying a newly-discovered dependency."""
        analysis = {
            "impact": {
                "blast_radius": 0.1, "affected_nodes": 1, "total_nodes": 10,
                "critical_nodes": ["db-main"], "average_metric_impact": 0.6,
            },
            "recovery": {
                "recovered_nodes": 1, "total_recovery_nodes": 1,
                "average_recovery_seconds": 10.0, "max_recovery_seconds": 15.0,
                "failed_recoveries": [],
            },
            "risk": {"level": "low", "reason": "Limited impact observed."},
            "recommendations": [],
        }
        body = test_client.post(
            "/api/experiments/suggest-next?last_target_node=db-main", json=analysis
        ).json()
        assert body["suggested_experiment"]["target_node"] == "db-main"
        assert "remains the only critical component" in body["reason"]

    def test_without_last_target_node_behavior_is_unchanged(self, test_client):
        """Omitting last_target_node (the pre-existing contract) must keep
        suggesting the first critical node, exactly as before."""
        analysis = {
            "impact": {
                "blast_radius": 0.4, "affected_nodes": 2, "total_nodes": 10,
                "critical_nodes": ["db-main", "orders"], "average_metric_impact": 0.6,
            },
            "recovery": {
                "recovered_nodes": 2, "total_recovery_nodes": 2,
                "average_recovery_seconds": 10.0, "max_recovery_seconds": 15.0,
                "failed_recoveries": [],
            },
            "risk": {"level": "moderate", "reason": "Notable impact observed."},
            "recommendations": [],
        }
        body = test_client.post("/api/experiments/suggest-next", json=analysis).json()
        assert body["suggested_experiment"]["target_node"] == "db-main"

    def test_last_target_node_skipped_in_failed_recoveries_too(self, test_client):
        analysis = {
            "impact": {
                "blast_radius": 0.3, "affected_nodes": 2, "total_nodes": 10,
                "critical_nodes": [], "average_metric_impact": 0.3,
            },
            "recovery": {
                "recovered_nodes": 0, "total_recovery_nodes": 2,
                "average_recovery_seconds": 20.0, "max_recovery_seconds": 30.0,
                "failed_recoveries": ["cart", "orders"],
            },
            "risk": {"level": "high", "reason": "Recovery failed."},
            "recommendations": [],
        }
        body = test_client.post(
            "/api/experiments/suggest-next?last_target_node=cart", json=analysis
        ).json()
        assert body["recommendation_type"] == "recovery_validation"
        assert body["suggested_experiment"]["target_node"] == "orders"

    def test_system_id_for_a_system_with_no_history_behaves_like_analysis_only(
        self, test_client
    ):
        """system_id is real data, not a required parameter — a system with
        no persisted runs yet must fall back to exactly today's behavior."""
        analysis = {
            "impact": {
                "blast_radius": 0.4, "affected_nodes": 2, "total_nodes": 10,
                "critical_nodes": ["db-main", "orders"], "average_metric_impact": 0.6,
            },
            "recovery": {
                "recovered_nodes": 2, "total_recovery_nodes": 2,
                "average_recovery_seconds": 10.0, "max_recovery_seconds": 15.0,
                "failed_recoveries": [],
            },
            "risk": {"level": "moderate", "reason": "Notable impact observed."},
            "recommendations": [],
        }
        body = test_client.post(
            "/api/experiments/suggest-next?system_id=sys-brand-new-no-history", json=analysis
        ).json()
        assert body["suggested_experiment"]["target_node"] == "db-main"
        assert body["suggested_experiment"]["type"] == "service_down"

    @staticmethod
    def _small_system(system_id: str) -> dict:
        """A tiny, uniquely-identified system so these tests' persisted
        history can never be contaminated by other tests sharing demo_system
        / sys-demo in the same session-scoped database."""
        return {
            "id": system_id,
            "name": "Suggest-Next History Test System",
            "nodes": [
                {"id": "alpha", "name": "Alpha", "node_type": "service"},
                {"id": "beta", "name": "Beta", "node_type": "service"},
                {"id": "gamma", "name": "Gamma", "node_type": "service"},
            ],
            "dependencies": [],
        }

    def test_system_id_prefers_a_never_tested_critical_node_over_an_already_tested_one(
        self, test_client
    ):
        """Real regression coverage for the history-aware upgrade: without
        system_id, 'alpha' would always win (it's first in critical_nodes
        and isn't last_target_node). With system_id, since 'alpha' was
        already tested by a real prior run and 'beta' was not, 'beta' must
        win — evidence the suggestion actually consulted persisted history,
        not just the analysis payload."""
        system_id = "sys-suggest-history-node-1"
        system = self._small_system(system_id)

        run_payload = {
            "system": system,
            "experiment": {
                "id": "exp-suggest-history-alpha",
                "system_id": system_id,
                "target_node": "alpha",
                "type": "service_down",
                "duration_seconds": 30,
            },
        }
        assert test_client.post("/api/experiments/run", json=run_payload).status_code == 200

        analysis = {
            "impact": {
                "blast_radius": 0.4, "affected_nodes": 2, "total_nodes": 3,
                "critical_nodes": ["alpha", "beta"], "average_metric_impact": 0.6,
            },
            "recovery": {
                "recovered_nodes": 2, "total_recovery_nodes": 2,
                "average_recovery_seconds": 10.0, "max_recovery_seconds": 15.0,
                "failed_recoveries": [],
            },
            "risk": {"level": "moderate", "reason": "Notable impact observed."},
            "recommendations": [],
        }

        without_history = test_client.post(
            "/api/experiments/suggest-next?last_target_node=gamma", json=analysis
        ).json()
        assert without_history["suggested_experiment"]["target_node"] == "alpha"

        with_history = test_client.post(
            f"/api/experiments/suggest-next?last_target_node=gamma&system_id={system_id}",
            json=analysis,
        ).json()
        assert with_history["suggested_experiment"]["target_node"] == "beta"

    def test_system_id_varies_suggested_type_instead_of_always_service_down(
        self, test_client
    ):
        """A node already tested with service_down should be suggested with
        a different experiment type next, when system_id gives access to
        that history — proven against a real persisted run, not a mock."""
        system_id = "sys-suggest-history-node-2"
        system = self._small_system(system_id)

        run_payload = {
            "system": system,
            "experiment": {
                "id": "exp-suggest-history-type",
                "system_id": system_id,
                "target_node": "alpha",
                "type": "service_down",
                "duration_seconds": 30,
            },
        }
        assert test_client.post("/api/experiments/run", json=run_payload).status_code == 200

        analysis = {
            "impact": {
                "blast_radius": 0.2, "affected_nodes": 1, "total_nodes": 3,
                "critical_nodes": ["alpha"], "average_metric_impact": 0.3,
            },
            "recovery": {
                "recovered_nodes": 1, "total_recovery_nodes": 1,
                "average_recovery_seconds": 8.0, "max_recovery_seconds": 8.0,
                "failed_recoveries": [],
            },
            "risk": {"level": "low", "reason": "Limited impact observed."},
            "recommendations": [],
        }

        body = test_client.post(
            f"/api/experiments/suggest-next?system_id={system_id}", json=analysis
        ).json()
        assert body["suggested_experiment"]["target_node"] == "alpha"
        assert body["suggested_experiment"]["type"] != "service_down"


# ── Scenario comparison endpoint ──────────────────────────────────────────────

class TestCompareExperimentsEndpoint:
    def _run_and_get_id(self, test_client, demo_system, exp_id: str, exp_type: str, target: str) -> str:
        payload = {
            "system": demo_system.model_dump(mode="json"),
            "experiment": {
                "id": exp_id,
                "system_id": demo_system.id,
                "target_node": target,
                "type": exp_type,
                "duration_seconds": 30,
            },
        }
        body = test_client.post("/api/experiments/run", json=payload).json()
        assert body["success"] is True
        return body["data"]["run"]["id"]

    def test_compare_two_runs_returns_200(self, test_client, demo_system):
        run_id_a = self._run_and_get_id(test_client, demo_system, "exp-cmp-1", "service_down", "auth")
        run_id_b = self._run_and_get_id(test_client, demo_system, "exp-cmp-2", "latency_spike", "auth")
        response = test_client.post("/api/experiments/compare", json={"run_ids": [run_id_a, run_id_b]})
        assert response.status_code == 200

    def test_compare_returns_runs_list(self, test_client, demo_system):
        run_id_a = self._run_and_get_id(test_client, demo_system, "exp-cmp-3", "service_down", "gateway")
        run_id_b = self._run_and_get_id(test_client, demo_system, "exp-cmp-4", "traffic_spike", "gateway")
        body = test_client.post("/api/experiments/compare", json={"run_ids": [run_id_a, run_id_b]}).json()
        assert "runs" in body
        assert isinstance(body["runs"], list)
        assert len(body["runs"]) == 2

    def test_compare_runs_contain_full_experiment_data(self, test_client, demo_system):
        run_id_a = self._run_and_get_id(test_client, demo_system, "exp-cmp-5", "resource_exhaustion", "auth")
        run_id_b = self._run_and_get_id(test_client, demo_system, "exp-cmp-6", "traffic_spike", "auth")
        body = test_client.post("/api/experiments/compare", json={"run_ids": [run_id_a, run_id_b]}).json()
        for run_data in body["runs"]:
            assert "run"              in run_data
            assert "resilience_score" in run_data
            assert "analysis"         in run_data
            assert "ai_analysis"      in run_data

    def test_compare_unknown_run_id_returns_404(self, test_client):
        response = test_client.post(
            "/api/experiments/compare",
            json={"run_ids": ["run-does-not-exist-a", "run-does-not-exist-b"]},
        )
        assert response.status_code == 404

    def test_compare_single_run_id_returns_422(self, test_client, demo_system):
        """Pydantic min_length=2 must reject a list with only one run_id."""
        run_id = self._run_and_get_id(test_client, demo_system, "exp-cmp-7", "service_down", "gateway")
        response = test_client.post("/api/experiments/compare", json={"run_ids": [run_id]})
        assert response.status_code == 422

    def test_compare_three_runs_returns_correct_count(self, test_client, demo_system):
        run_a = self._run_and_get_id(test_client, demo_system, "exp-cmp-8",  "service_down", "auth")
        run_b = self._run_and_get_id(test_client, demo_system, "exp-cmp-9",  "latency_spike", "catalog")
        run_c = self._run_and_get_id(test_client, demo_system, "exp-cmp-10", "traffic_spike", "orders")
        body = test_client.post("/api/experiments/compare", json={"run_ids": [run_a, run_b, run_c]}).json()
        assert len(body["runs"]) == 3

    def test_list_experiments_filtered_by_system_id_returns_list(
        self, test_client
    ):
        response = test_client.get("/api/experiments/?system_id=sys-demo")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_run_then_list_shows_persisted_result(
        self, test_client, run_experiment_payload_db_main
    ):
        """After running an experiment, it must appear in the history list."""
        # Run it
        run_resp = test_client.post(
            "/api/experiments/run", json=run_experiment_payload_db_main
        )
        assert run_resp.status_code == 200
        run_id = run_resp.json()["data"]["run"]["id"]

        # Fetch history filtered by system id
        list_resp = test_client.get("/api/experiments/?system_id=sys-demo")
        assert list_resp.status_code == 200
        history_run_ids = [item["run"]["id"] for item in list_resp.json()]
        assert run_id in history_run_ids
