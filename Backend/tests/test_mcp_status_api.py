"""
Tests for GET /api/mcp/status — the real, observable signal the frontend's
"IBM Bob via MCP" indicator is built on.
"""

import os
import tempfile

import pytest


@pytest.fixture
def isolated_persistence(monkeypatch):
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
    tmp.close()
    monkeypatch.setenv("CODETWIN_DATABASE_PATH", tmp.name)
    yield tmp.name


class TestMcpStatusEndpoint:
    def test_server_available_is_true_in_this_installation(self, test_client):
        response = test_client.get("/api/mcp/status")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["server_available"] is True

    def test_no_activity_yet_reports_null(self, isolated_persistence):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        body = client.get("/api/mcp/status").json()
        assert body["data"]["last_activity"] is None

    def test_recorded_activity_is_reported_with_a_recent_seconds_ago(self, isolated_persistence):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.services.persistence_service import PersistenceService

        PersistenceService().record_mcp_activity("faultlens_get_context", "sys-status-test")

        client = TestClient(app)
        body = client.get("/api/mcp/status").json()
        activity = body["data"]["last_activity"]
        assert activity is not None
        assert activity["tool_name"] == "faultlens_get_context"
        assert activity["system_id"] == "sys-status-test"
        assert activity["seconds_ago"] < 5

    def test_only_the_most_recent_activity_is_reported(self, isolated_persistence):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.services.persistence_service import PersistenceService

        persistence = PersistenceService()
        persistence.record_mcp_activity("chaos_run_experiment", "sys-a")
        persistence.record_mcp_activity("faultlens_get_context", "sys-b")

        client = TestClient(app)
        body = client.get("/api/mcp/status").json()
        assert body["data"]["last_activity"]["tool_name"] == "faultlens_get_context"
        assert body["data"]["last_activity"]["system_id"] == "sys-b"
