"""Canonical demo Digital Twin used to seed a fresh backend on first run."""

from app.models.dependency import Dependency
from app.models.node import Node
from app.models.system import System

DEMO_SYSTEM_ID = "sys-demo"


def build_demo_system() -> System:
    """
    Builds the FaultLens demo system: a 10-node e-commerce architecture
    with realistic dependency propagation, deep enough to demonstrate a
    multi-hop blast radius when the database or a core service goes down.

    Mirrors the topology the frontend ships as its default state
    (Frontend/src/store/experimentStore.ts) so the UI looks identical
    whether it loaded from a fresh backend seed or its own local fallback.
    """

    nodes = [
        Node(
            id="gateway",
            name="API Gateway",
            node_type="gateway",
            description="Public entry point that routes requests to internal services.",
        ),
        Node(
            id="auth",
            name="Auth Service",
            node_type="service",
            description="Authenticates requests and issues session tokens.",
        ),
        Node(
            id="catalog",
            name="Catalog Service",
            node_type="service",
            description="Serves product listings and inventory data.",
        ),
        Node(
            id="cart",
            name="Cart Service",
            node_type="service",
            description="Manages active shopping carts.",
        ),
        Node(
            id="orders",
            name="Order Service",
            node_type="service",
            description="Creates and tracks customer orders.",
        ),
        Node(
            id="payments",
            name="Payment Service",
            node_type="service",
            description="Processes payment charges for orders.",
        ),
        Node(
            id="notifications",
            name="Notification Service",
            node_type="service",
            description="Sends order and account notifications to customers.",
        ),
        Node(
            id="db-main",
            name="Primary Database",
            node_type="database",
            description="Primary relational store for auth, catalog, and order data.",
        ),
        Node(
            id="db-cache",
            name="Redis Cache",
            node_type="cache",
            description="In-memory cache backing the cart service.",
        ),
        Node(
            id="queue",
            name="Message Queue",
            node_type="queue",
            description="Asynchronous message bus for orders and notifications.",
        ),
    ]

    dependencies = [
        Dependency(source="gateway", target="auth"),
        Dependency(source="gateway", target="catalog"),
        Dependency(source="gateway", target="cart"),
        Dependency(source="gateway", target="orders"),
        Dependency(source="cart", target="db-cache"),
        Dependency(source="catalog", target="db-main"),
        Dependency(source="orders", target="db-main"),
        Dependency(source="orders", target="payments"),
        Dependency(source="orders", target="queue"),
        Dependency(source="notifications", target="queue"),
        Dependency(source="auth", target="db-main"),
    ]

    return System(
        id=DEMO_SYSTEM_ID,
        name="E-Commerce Platform",
        nodes=nodes,
        dependencies=dependencies,
    )
