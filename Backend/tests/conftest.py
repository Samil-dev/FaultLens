"""
Shared pytest fixtures for the FaultLens / CodeTwin backend test suite.

All fixtures build real production objects — no mocking of business logic.
The TestClient is backed by the real FastAPI app; only the SQLite database
path is redirected to a temp file so tests never touch the real codetwin.sqlite3.
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.models.dependency import Dependency
from app.models.experiment import Experiment
from app.models.node import Node
from app.models.system import System


# ── Demo system ───────────────────────────────────────────────────────────────
# Mirrors the 10-node e-commerce topology used by the frontend.
# Dependencies encode: source DEPENDS ON target.

@pytest.fixture(scope="session")
def demo_system() -> System:
    nodes = [
        Node(id="gateway",       name="API Gateway",           node_type="gateway"),
        Node(id="auth",          name="Auth Service",           node_type="service"),
        Node(id="catalog",       name="Catalog Service",        node_type="service"),
        Node(id="cart",          name="Cart Service",           node_type="service"),
        Node(id="orders",        name="Order Service",          node_type="service"),
        Node(id="payments",      name="Payment Service",        node_type="service"),
        Node(id="notifications", name="Notification Service",   node_type="service"),
        Node(id="db-main",       name="Primary Database",       node_type="database"),
        Node(id="db-cache",      name="Redis Cache",            node_type="cache"),
        Node(id="queue",         name="Message Queue",          node_type="queue"),
    ]
    dependencies = [
        Dependency(source="gateway",       target="auth"),
        Dependency(source="gateway",       target="catalog"),
        Dependency(source="gateway",       target="cart"),
        Dependency(source="gateway",       target="orders"),
        Dependency(source="cart",          target="db-cache"),
        Dependency(source="catalog",       target="db-main"),
        Dependency(source="orders",        target="db-main"),
        Dependency(source="orders",        target="payments"),
        Dependency(source="orders",        target="queue"),
        Dependency(source="notifications", target="queue"),
        Dependency(source="auth",          target="db-main"),
    ]
    return System(id="sys-demo", name="E-Commerce Platform", nodes=nodes, dependencies=dependencies)


# ── Experiment factories ──────────────────────────────────────────────────────

@pytest.fixture
def service_down_db_main(demo_system: System) -> Experiment:
    """service_down targeting db-main — maximum propagation in the demo topology."""
    return Experiment(
        id="exp-test-db-main",
        system_id=demo_system.id,
        target_node="db-main",
        type="service_down",
        duration_seconds=30,
    )


@pytest.fixture
def service_down_gateway(demo_system: System) -> Experiment:
    """service_down targeting gateway — gateway has no dependents (leaf from reverse-graph)."""
    return Experiment(
        id="exp-test-gateway",
        system_id=demo_system.id,
        target_node="gateway",
        type="service_down",
        duration_seconds=30,
    )


@pytest.fixture
def service_down_auth(demo_system: System) -> Experiment:
    """service_down targeting auth — auth has one dependent (gateway)."""
    return Experiment(
        id="exp-test-auth",
        system_id=demo_system.id,
        target_node="auth",
        type="service_down",
        duration_seconds=30,
    )


@pytest.fixture
def latency_spike_db_main(demo_system: System) -> Experiment:
    """latency_spike targeting db-main — maximum propagation in the demo topology."""
    return Experiment(
        id="exp-test-latency-db-main",
        system_id=demo_system.id,
        target_node="db-main",
        type="latency_spike",
        duration_seconds=30,
    )


@pytest.fixture
def latency_spike_gateway(demo_system: System) -> Experiment:
    """latency_spike targeting gateway — no affected nodes."""
    return Experiment(
        id="exp-test-latency-gateway",
        system_id=demo_system.id,
        target_node="gateway",
        type="latency_spike",
        duration_seconds=30,
    )


@pytest.fixture
def resource_exhaustion_db_main(demo_system: System) -> Experiment:
    """resource_exhaustion targeting db-main."""
    return Experiment(
        id="exp-test-resource-db-main",
        system_id=demo_system.id,
        target_node="db-main",
        type="resource_exhaustion",
        duration_seconds=30,
    )


@pytest.fixture
def resource_exhaustion_gateway(demo_system: System) -> Experiment:
    """resource_exhaustion targeting gateway — no affected nodes."""
    return Experiment(
        id="exp-test-resource-gateway",
        system_id=demo_system.id,
        target_node="gateway",
        type="resource_exhaustion",
        duration_seconds=30,
    )


@pytest.fixture
def traffic_spike_db_main(demo_system: System) -> Experiment:
    """traffic_spike targeting db-main — maximum propagation in the demo topology."""
    return Experiment(
        id="exp-test-traffic-db-main",
        system_id=demo_system.id,
        target_node="db-main",
        type="traffic_spike",
        duration_seconds=30,
    )


@pytest.fixture
def traffic_spike_gateway(demo_system: System) -> Experiment:
    """traffic_spike targeting gateway — no affected nodes."""
    return Experiment(
        id="exp-test-traffic-gateway",
        system_id=demo_system.id,
        target_node="gateway",
        type="traffic_spike",
        duration_seconds=30,
    )


# ── FastAPI TestClient ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_client() -> TestClient:
    """
    A FastAPI TestClient backed by the real app.

    CODETWIN_DATABASE_PATH is set to a per-session temp file so tests never
    touch the real codetwin.sqlite3 and each test run starts from a clean slate.
    """
    # Must be set BEFORE importing app.main so PersistenceService picks it up.
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
    tmp.close()
    os.environ["CODETWIN_DATABASE_PATH"] = tmp.name

    from app.main import app
    return TestClient(app)


# ── Minimal valid request payloads (as plain dicts for HTTP POST) ─────────────

@pytest.fixture
def run_experiment_payload_db_main(demo_system: System) -> dict:
    """Valid POST /api/experiments/run body targeting db-main."""
    return {
        "system": demo_system.model_dump(mode="json"),
        "experiment": {
            "id": "exp-http-db-main",
            "system_id": demo_system.id,
            "target_node": "db-main",
            "type": "service_down",
            "duration_seconds": 30,
        },
    }


@pytest.fixture
def run_experiment_payload_gateway(demo_system: System) -> dict:
    """Valid POST /api/experiments/run body targeting gateway (leaf node)."""
    return {
        "system": demo_system.model_dump(mode="json"),
        "experiment": {
            "id": "exp-http-gateway",
            "system_id": demo_system.id,
            "target_node": "gateway",
            "type": "service_down",
            "duration_seconds": 30,
        },
    }
