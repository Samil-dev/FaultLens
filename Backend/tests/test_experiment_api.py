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
        ai = body["data"]["ai_analysis"]
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
        summary = body["data"]["ai_analysis"]["summary"].lower()
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
        root_cause = body["data"]["ai_analysis"]["root_cause"].lower()
        # Evidence-based root cause must mention the target node
        assert "auth" in root_cause


# ── Experiment history endpoint ───────────────────────────────────────────────

class TestListExperimentsEndpoint:
    def test_list_experiments_returns_200(self, test_client):
        response = test_client.get("/api/experiments/")
        assert response.status_code == 200

    def test_list_experiments_returns_list(self, test_client):
        body = test_client.get("/api/experiments/").json()
        assert isinstance(body, list)


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
