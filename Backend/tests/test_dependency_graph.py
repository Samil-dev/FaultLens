"""
Unit tests for DependencyGraph — covering build, traversal, and deduplication.

All expected values are derived from the demo system topology and verified
against the corrected get_affected_nodes() implementation.

Demo system dependency edges (source DEPENDS ON target):
  gateway  -> auth
  gateway  -> catalog
  gateway  -> cart
  gateway  -> orders
  cart     -> db-cache
  catalog  -> db-main
  orders   -> db-main
  orders   -> payments
  orders   -> queue
  notifications -> queue
  auth     -> db-main

Reverse-graph (who depends on me):
  auth      <- [gateway]
  catalog   <- [gateway]
  cart      <- [gateway]
  orders    <- [gateway]
  db-cache  <- [cart]
  db-main   <- [catalog, orders, auth]
  payments  <- [orders]
  queue     <- [orders, notifications]

Transitive affected-node ground truth (fixed, no duplicates):
  gateway       -> []
  auth          -> [gateway]
  catalog       -> [gateway]
  cart          -> [gateway]
  orders        -> [gateway]
  payments      -> [gateway, orders]          (orders->gateway)
  notifications -> []
  db-main       -> [auth, catalog, gateway, orders]  (all three->gateway)
  db-cache      -> [cart, gateway]            (cart->gateway)
  queue         -> [gateway, notifications, orders]  (orders->gateway)
"""

import pytest

from app.graph.dependency_graph import DependencyGraph
from app.models.dependency import Dependency
from app.models.node import Node
from app.models.system import System


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def graph(demo_system: System) -> DependencyGraph:
    return DependencyGraph(demo_system)


# ── Build graph ───────────────────────────────────────────────────────────────

class TestBuildGraph:
    def test_graph_contains_all_nodes(self, graph, demo_system):
        for node in demo_system.nodes:
            assert node.id in graph.graph

    def test_graph_node_count_matches_system(self, graph, demo_system):
        assert len(graph.graph) == len(demo_system.nodes)

    def test_forward_edge_gateway_to_auth(self, graph):
        assert "auth" in graph.graph["gateway"]

    def test_forward_edge_catalog_to_db_main(self, graph):
        assert "db-main" in graph.graph["catalog"]

    def test_leaf_nodes_have_empty_adjacency(self, graph):
        # gateway has no outgoing edges that OTHER nodes point back to —
        # but gateway itself has many outgoing edges; db-main is a leaf
        # in the FORWARD graph (nothing depends-on db-main from db-main).
        assert graph.graph["db-main"] == []

    def test_isolated_node_has_empty_adjacency(self):
        """A node with no dependencies and no dependents appears with []."""
        system = System(
            id="s1",
            name="Tiny",
            nodes=[Node(id="solo", name="Solo", node_type="service")],
            dependencies=[],
        )
        g = DependencyGraph(system)
        assert g.graph["solo"] == []


# ── get_affected_nodes — no duplicates ───────────────────────────────────────

class TestNoduplicates:
    def test_db_main_affected_has_no_duplicates(self, graph):
        aff = graph.get_affected_nodes("db-main")
        assert len(aff) == len(set(aff)), f"Duplicates found: {aff}"

    def test_queue_affected_has_no_duplicates(self, graph):
        aff = graph.get_affected_nodes("queue")
        assert len(aff) == len(set(aff)), f"Duplicates found: {aff}"

    def test_db_cache_affected_has_no_duplicates(self, graph):
        aff = graph.get_affected_nodes("db-cache")
        assert len(aff) == len(set(aff)), f"Duplicates found: {aff}"

    def test_payments_affected_has_no_duplicates(self, graph):
        aff = graph.get_affected_nodes("payments")
        assert len(aff) == len(set(aff)), f"Duplicates found: {aff}"

    def test_all_nodes_produce_no_duplicates(self, graph, demo_system):
        """Parametric check — every possible failure target must be duplicate-free."""
        for node in demo_system.nodes:
            aff = graph.get_affected_nodes(node.id)
            assert len(aff) == len(set(aff)), (
                f"Duplicates in affected_nodes for target '{node.id}': {aff}"
            )


# ── get_affected_nodes — correct counts ───────────────────────────────────────

class TestAffectedCounts:
    def test_gateway_has_zero_affected_nodes(self, graph):
        """gateway has no reverse-dependents; nothing depends on it."""
        assert graph.get_affected_nodes("gateway") == []

    def test_notifications_has_zero_affected_nodes(self, graph):
        """notifications has no reverse-dependents; nothing in the system depends on it."""
        assert graph.get_affected_nodes("notifications") == []

    def test_auth_has_one_affected_node(self, graph):
        """Only gateway depends on auth."""
        assert len(graph.get_affected_nodes("auth")) == 1

    def test_catalog_has_one_affected_node(self, graph):
        """Only gateway depends on catalog."""
        assert len(graph.get_affected_nodes("catalog")) == 1

    def test_cart_has_one_affected_node(self, graph):
        """Only gateway depends on cart."""
        assert len(graph.get_affected_nodes("cart")) == 1

    def test_orders_has_one_affected_node(self, graph):
        """Only gateway depends on orders directly; payments and queue are downstream of orders, not upstream."""
        assert len(graph.get_affected_nodes("orders")) == 1

    def test_db_main_has_four_affected_nodes(self, graph):
        """
        db-main is depended on by catalog, orders, auth (direct).
        Each of those is depended on by gateway (transitive).
        Total unique: auth, catalog, orders, gateway = 4.
        """
        assert len(graph.get_affected_nodes("db-main")) == 4

    def test_db_cache_has_two_affected_nodes(self, graph):
        """
        db-cache <- cart <- gateway
        = 2 unique affected nodes.
        """
        assert len(graph.get_affected_nodes("db-cache")) == 2

    def test_queue_has_three_affected_nodes(self, graph):
        """
        queue <- orders <- gateway    (orders->queue, gateway->orders)
        queue <- notifications         (notifications->queue)
        = orders, notifications, gateway = 3 unique.
        """
        assert len(graph.get_affected_nodes("queue")) == 3

    def test_payments_has_two_affected_nodes(self, graph):
        """
        payments <- orders <- gateway
        = 2 unique: orders, gateway.
        """
        assert len(graph.get_affected_nodes("payments")) == 2


# ── get_affected_nodes — correct membership ───────────────────────────────────

class TestAffectedMembership:
    def test_auth_affected_contains_gateway(self, graph):
        assert "gateway" in graph.get_affected_nodes("auth")

    def test_db_main_affected_contains_all_four(self, graph):
        aff = set(graph.get_affected_nodes("db-main"))
        assert aff == {"auth", "catalog", "orders", "gateway"}

    def test_db_main_affected_does_not_contain_target(self, graph):
        assert "db-main" not in graph.get_affected_nodes("db-main")

    def test_db_cache_affected_contains_cart_and_gateway(self, graph):
        aff = set(graph.get_affected_nodes("db-cache"))
        assert aff == {"cart", "gateway"}

    def test_queue_affected_contains_correct_set(self, graph):
        aff = set(graph.get_affected_nodes("queue"))
        assert aff == {"orders", "notifications", "gateway"}

    def test_payments_affected_contains_orders_and_gateway(self, graph):
        aff = set(graph.get_affected_nodes("payments"))
        assert aff == {"orders", "gateway"}

    def test_target_never_appears_in_own_affected_nodes(self, graph, demo_system):
        """No node should appear in its own affected-nodes list."""
        for node in demo_system.nodes:
            aff = graph.get_affected_nodes(node.id)
            assert node.id not in aff, (
                f"Target '{node.id}' appeared in its own affected_nodes: {aff}"
            )


# ── get_affected_nodes — edge cases ───────────────────────────────────────────

class TestEdgeCases:
    def test_unknown_node_returns_empty_list(self, graph):
        assert graph.get_affected_nodes("nonexistent-node") == []

    def test_single_node_system_returns_empty(self):
        system = System(
            id="s1",
            name="Single",
            nodes=[Node(id="only", name="Only", node_type="service")],
            dependencies=[],
        )
        g = DependencyGraph(system)
        assert g.get_affected_nodes("only") == []

    def test_linear_chain_full_propagation(self):
        """
        a -> b -> c  (a depends on b, b depends on c)
        Failing c: affected = [b, a]  (b depends on c; a depends on b)
        """
        system = System(
            id="chain",
            name="Chain",
            nodes=[
                Node(id="a", name="A", node_type="service"),
                Node(id="b", name="B", node_type="service"),
                Node(id="c", name="C", node_type="service"),
            ],
            dependencies=[
                Dependency(source="a", target="b"),
                Dependency(source="b", target="c"),
            ],
        )
        g = DependencyGraph(system)
        aff = g.get_affected_nodes("c")
        assert set(aff) == {"a", "b"}
        assert len(aff) == 2

    def test_diamond_topology_no_duplicates(self):
        """
        Diamond: a->b, a->c, b->d, c->d
        Failing d: b and c both depend on d; a depends on both.
        Expected: {b, c, a}, each exactly once.
        """
        system = System(
            id="diamond",
            name="Diamond",
            nodes=[
                Node(id="a", name="A", node_type="service"),
                Node(id="b", name="B", node_type="service"),
                Node(id="c", name="C", node_type="service"),
                Node(id="d", name="D", node_type="service"),
            ],
            dependencies=[
                Dependency(source="a", target="b"),
                Dependency(source="a", target="c"),
                Dependency(source="b", target="d"),
                Dependency(source="c", target="d"),
            ],
        )
        g = DependencyGraph(system)
        aff = g.get_affected_nodes("d")
        assert len(aff) == len(set(aff)), f"Duplicates in diamond: {aff}"
        assert set(aff) == {"a", "b", "c"}

    def test_wide_fan_in_no_duplicates(self):
        """
        Many nodes all depending on one shared node:
        b->a, c->a, d->a, e->a
        Failing a: affected = {b, c, d, e}, each once.
        """
        system = System(
            id="fan",
            name="FanIn",
            nodes=[Node(id=x, name=x, node_type="service") for x in "abcde"],
            dependencies=[
                Dependency(source="b", target="a"),
                Dependency(source="c", target="a"),
                Dependency(source="d", target="a"),
                Dependency(source="e", target="a"),
            ],
        )
        g = DependencyGraph(system)
        aff = g.get_affected_nodes("a")
        assert len(aff) == len(set(aff))
        assert set(aff) == {"b", "c", "d", "e"}

    def test_return_type_is_list(self, graph):
        assert isinstance(graph.get_affected_nodes("gateway"), list)
