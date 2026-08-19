"""
Tests for POST/GET /api/systems/ — architecture import and validation.

Exercises the real FastAPI app + real Pydantic validation (app.models.system),
not the validator function in isolation, so these tests catch contract-level
regressions (status codes, error shapes) as well as logic bugs.

`System` is used directly as the request body type for POST /api/systems/, so
its model_validator errors are raised during FastAPI's own request-body
parsing — Pydantic wraps them into a ValidationError before the endpoint
function ever runs, which FastAPI reports as 422 with the standard
`{"detail": [{"msg": "Value error, <message>", ...}]}` shape. This is
different from errors raised *inside* an endpoint body (e.g. a ValueError
raised by a service call), which are caught by the app's custom
`value_error_handler` in app.main and reported as 400 with
`{"success": false, "error": {"message": ...}}` instead.
"""


def _validation_message(response) -> str:
    return response.json()["detail"][0]["msg"]


def _valid_system(system_id: str) -> dict:
    return {
        "id": system_id,
        "name": "Test System",
        "nodes": [
            {"id": "n1", "name": "Node One", "node_type": "service"},
            {"id": "n2", "name": "Node Two", "node_type": "database"},
        ],
        "dependencies": [
            {"source": "n1", "target": "n2", "type": "depends_on"},
        ],
    }


class TestCreateSystemValid:
    def test_valid_system_is_accepted(self, test_client):
        response = test_client.post("/api/systems/", json=_valid_system("sys-valid-1"))
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        assert body["error"] is None
        assert body["data"]["id"] == "sys-valid-1"
        assert len(body["data"]["nodes"]) == 2

    def test_system_with_no_dependencies_is_accepted(self, test_client):
        payload = _valid_system("sys-valid-no-deps")
        payload["dependencies"] = []
        response = test_client.post("/api/systems/", json=payload)
        assert response.status_code == 200
        assert response.json()["data"]["dependencies"] == []

    def test_isolated_node_with_no_dependencies_at_all_is_accepted(self, test_client):
        """A node with no incoming or outgoing dependency is a valid (if
        trivial) architecture — isolation alone is not corruption."""
        response = test_client.post(
            "/api/systems/",
            json={
                "id": "sys-valid-isolated",
                "name": "Isolated Node System",
                "nodes": [{"id": "solo", "name": "Solo Node", "node_type": "service"}],
                "dependencies": [],
            },
        )
        assert response.status_code == 200

    def test_created_system_is_retrievable_via_list(self, test_client):
        test_client.post("/api/systems/", json=_valid_system("sys-listable"))
        response = test_client.get("/api/systems/")
        assert response.status_code == 200
        ids = [s["id"] for s in response.json()]
        assert "sys-listable" in ids


class TestCreateSystemValidation:
    def test_duplicate_node_ids_are_rejected(self, test_client):
        payload = _valid_system("sys-dup-ids")
        payload["nodes"] = [
            {"id": "n1", "name": "Node One", "node_type": "service"},
            {"id": "n1", "name": "Node One Again", "node_type": "service"},
        ]
        payload["dependencies"] = []
        response = test_client.post("/api/systems/", json=payload)
        assert response.status_code == 422
        assert "unique" in _validation_message(response).lower()

    def test_dependency_source_referencing_missing_node_is_rejected(self, test_client):
        payload = _valid_system("sys-bad-source")
        payload["dependencies"] = [{"source": "does-not-exist", "target": "n2", "type": "depends_on"}]
        response = test_client.post("/api/systems/", json=payload)
        assert response.status_code == 422
        assert "does-not-exist" in _validation_message(response)

    def test_dependency_target_referencing_missing_node_is_rejected(self, test_client):
        """Regression test: the model_validator used to check `source` twice
        instead of checking `target`, so a dependency pointing at a
        nonexistent target node was silently accepted."""
        payload = _valid_system("sys-bad-target")
        payload["dependencies"] = [{"source": "n1", "target": "does-not-exist", "type": "depends_on"}]
        response = test_client.post("/api/systems/", json=payload)
        assert response.status_code == 422
        assert "does-not-exist" in _validation_message(response)

    def test_cyclic_dependency_graph_is_rejected(self, test_client):
        payload = _valid_system("sys-cycle")
        payload["nodes"] = [
            {"id": "a", "name": "A", "node_type": "service"},
            {"id": "b", "name": "B", "node_type": "service"},
            {"id": "c", "name": "C", "node_type": "service"},
        ]
        payload["dependencies"] = [
            {"source": "a", "target": "b", "type": "depends_on"},
            {"source": "b", "target": "c", "type": "depends_on"},
            {"source": "c", "target": "a", "type": "depends_on"},
        ]
        response = test_client.post("/api/systems/", json=payload)
        assert response.status_code == 422
        assert "cycle" in _validation_message(response).lower()

    def test_empty_architecture_is_rejected(self, test_client):
        response = test_client.post(
            "/api/systems/",
            json={"id": "sys-empty", "name": "Empty System", "nodes": [], "dependencies": []},
        )
        assert response.status_code == 422
        assert "node" in _validation_message(response).lower()

    def test_empty_node_id_is_rejected(self, test_client):
        payload = _valid_system("sys-empty-node-id")
        payload["nodes"][0]["id"] = ""
        response = test_client.post("/api/systems/", json=payload)
        assert response.status_code == 422

    def test_missing_required_fields_returns_422(self, test_client):
        response = test_client.post("/api/systems/", json={"nodes": [], "dependencies": []})
        assert response.status_code == 422

    def test_malformed_json_body_returns_422(self, test_client):
        response = test_client.post(
            "/api/systems/",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
