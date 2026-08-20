"""
Unit tests for ChaosEngine — service_down behavior.

These tests document and lock behavior after the DependencyGraph
deduplication fix (Phase 2A). Every assertion is derived from the
actual production code and the corrected graph traversal.

Key topology facts for the demo system (post-fix, no duplicates):
  db-main  -> 4 affected: auth, catalog, orders, gateway
  auth     -> 1 affected: gateway
  gateway  -> 0 affected (no dependents in the reverse graph)
  db-cache -> 2 affected: cart, gateway
  queue    -> 3 affected: orders, notifications, gateway
  payments -> 2 affected: orders, gateway
"""

import pytest

from app.chaos.chaos_engine import ChaosEngine
from app.models.experiment import Experiment
from app.models.simulation_event import SimulationEvent
from app.models.simulation_run import SimulationRun
from app.models.system import System


# ── Helper ────────────────────────────────────────────────────────────────────

def _run(system: System, experiment: Experiment):
    """Convenience wrapper — returns (run, events)."""
    engine = ChaosEngine(system)
    return engine.run(experiment)


# ── Basic return shape ─────────────────────────────────────────────────────────

class TestReturnShape:
    def test_returns_tuple_of_run_and_events(self, demo_system, service_down_db_main):
        result = _run(demo_system, service_down_db_main)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_run_is_simulation_run(self, demo_system, service_down_db_main):
        run, _ = _run(demo_system, service_down_db_main)
        assert isinstance(run, SimulationRun)

    def test_events_is_list_of_simulation_events(self, demo_system, service_down_db_main):
        _, events = _run(demo_system, service_down_db_main)
        assert isinstance(events, list)
        assert all(isinstance(e, SimulationEvent) for e in events)

    def test_run_status_is_completed(self, demo_system, service_down_db_main):
        run, _ = _run(demo_system, service_down_db_main)
        assert run.status == "completed"

    def test_run_experiment_id_matches(self, demo_system, service_down_db_main):
        run, _ = _run(demo_system, service_down_db_main)
        assert run.experiment_id == service_down_db_main.id

    def test_run_id_is_prefixed(self, demo_system, service_down_db_main):
        run, _ = _run(demo_system, service_down_db_main)
        assert run.id == f"run-{service_down_db_main.id}"

    def test_run_records_the_configured_duration(self, demo_system, service_down_db_main):
        """Regression test: duration_seconds used to influence the outcome
        without ever being persisted anywhere retrievable afterward — a
        SimulationRun (and therefore FaultLensContext) could never report
        what duration actually produced it."""
        run, _ = _run(demo_system, service_down_db_main)
        assert run.duration_seconds == service_down_db_main.duration_seconds
        assert run.duration_seconds == 30


# ── Events ────────────────────────────────────────────────────────────────────

class TestEvents:
    def test_first_event_is_failure_injected(self, demo_system, service_down_db_main):
        _, events = _run(demo_system, service_down_db_main)
        assert events[0].event_type == "failure_injected"

    def test_failure_injected_targets_correct_node(self, demo_system, service_down_db_main):
        _, events = _run(demo_system, service_down_db_main)
        failure_events = [e for e in events if e.event_type == "failure_injected"]
        assert len(failure_events) == 1
        assert failure_events[0].node_id == "db-main"

    def test_failure_injected_has_max_severity(self, demo_system, service_down_db_main):
        _, events = _run(demo_system, service_down_db_main)
        assert events[0].severity == 1.0

    def test_affected_nodes_each_get_node_degraded_event(self, demo_system, service_down_db_main):
        run, events = _run(demo_system, service_down_db_main)
        degraded_node_ids = {e.node_id for e in events if e.event_type == "node_degraded"}
        for node_id in run.affected_nodes:
            assert node_id in degraded_node_ids

    def test_total_event_count_equals_one_plus_affected(self, demo_system, service_down_db_main):
        # 1 failure_injected + 1 per affected node
        run, events = _run(demo_system, service_down_db_main)
        assert len(events) == 1 + len(run.affected_nodes)

    def test_node_degraded_severity_decreases_with_index(self, demo_system, service_down_db_main):
        _, events = _run(demo_system, service_down_db_main)
        degraded = [e for e in events if e.event_type == "node_degraded"]
        # severity = max(0.1, 1.0 - (index+1)*0.2), so first is always ≥ second
        assert degraded[0].severity >= degraded[1].severity

    def test_gateway_service_down_produces_no_node_degraded_events(
        self, demo_system, service_down_gateway
    ):
        """gateway has zero reverse-dependents so only 1 event is emitted."""
        _, events = _run(demo_system, service_down_gateway)
        assert len(events) == 1
        assert events[0].event_type == "failure_injected"
        assert events[0].node_id == "gateway"


# ── Affected nodes ────────────────────────────────────────────────────────────

class TestAffectedNodes:
    def test_db_main_produces_4_unique_affected_nodes(self, demo_system, service_down_db_main):
        """
        db-main has 3 direct dependents (auth, catalog, orders), each of which
        depends on gateway. The fixed BFS deduplicates at enqueue time, so
        gateway appears exactly once. Total: auth, catalog, orders, gateway = 4.
        """
        run, _ = _run(demo_system, service_down_db_main)
        assert len(run.affected_nodes) == 4

    def test_db_main_affected_nodes_have_no_duplicates(self, demo_system, service_down_db_main):
        run, _ = _run(demo_system, service_down_db_main)
        assert len(run.affected_nodes) == len(set(run.affected_nodes))

    def test_db_main_affected_includes_auth_catalog_orders_gateway(self, demo_system, service_down_db_main):
        run, _ = _run(demo_system, service_down_db_main)
        affected_set = set(run.affected_nodes)
        assert "auth"    in affected_set
        assert "catalog" in affected_set
        assert "orders"  in affected_set
        assert "gateway" in affected_set

    def test_target_node_not_in_affected_nodes(self, demo_system, service_down_db_main):
        """The target node (db-main) is never included in affected_nodes."""
        run, _ = _run(demo_system, service_down_db_main)
        assert "db-main" not in run.affected_nodes

    def test_gateway_has_zero_affected_nodes(self, demo_system, service_down_gateway):
        run, _ = _run(demo_system, service_down_gateway)
        assert run.affected_nodes == []

    def test_auth_has_one_affected_node(self, demo_system, service_down_auth):
        run, _ = _run(demo_system, service_down_auth)
        assert len(run.affected_nodes) == 1
        assert run.affected_nodes[0] == "gateway"


# ── Recoveries ────────────────────────────────────────────────────────────────

class TestRecoveries:
    def test_recovery_count_equals_one_plus_affected(self, demo_system, service_down_db_main):
        """1 entry for target + 1 per unique affected node (4 after fix = 5 total)."""
        run, _ = _run(demo_system, service_down_db_main)
        assert len(run.recoveries) == 1 + len(run.affected_nodes)
        assert len(run.recoveries) == 5

    def test_target_node_recovery_time_is_15_seconds(self, demo_system, service_down_db_main):
        run, _ = _run(demo_system, service_down_db_main)
        target_recovery = next(r for r in run.recoveries if r.node_id == "db-main")
        assert target_recovery.recovery_time_seconds == 15.0

    def test_all_recoveries_have_status_recovered(self, demo_system, service_down_db_main):
        run, _ = _run(demo_system, service_down_db_main)
        for recovery in run.recoveries:
            assert recovery.recovery_status == "recovered"

    def test_affected_node_recovery_times_start_at_8_seconds(
        self, demo_system, service_down_db_main
    ):
        run, _ = _run(demo_system, service_down_db_main)
        # Filter out the target node recovery (15.0s)
        affected_recoveries = [r for r in run.recoveries if r.node_id != "db-main"]
        # First affected node recovery = 8.0 + 0*0.2 = 8.0
        assert affected_recoveries[0].recovery_time_seconds == pytest.approx(8.0)

    def test_affected_node_recovery_times_increment_by_0_2(
        self, demo_system, service_down_db_main
    ):
        run, _ = _run(demo_system, service_down_db_main)
        affected_recoveries = [r for r in run.recoveries if r.node_id != "db-main"]
        for i, recovery in enumerate(affected_recoveries):
            expected = 8.0 + i * 0.2
            assert recovery.recovery_time_seconds == pytest.approx(expected)

    def test_gateway_target_has_single_recovery_entry(self, demo_system, service_down_gateway):
        """gateway has 0 affected nodes, so only 1 recovery record (the target itself)."""
        run, _ = _run(demo_system, service_down_gateway)
        assert len(run.recoveries) == 1
        assert run.recoveries[0].node_id == "gateway"
        assert run.recoveries[0].recovery_time_seconds == 15.0


# ── Duration has real, deterministic consequences ─────────────────────────────
# db-main's reverse-graph shape (see module docstring): direct dependents
# (depth 1) are auth/catalog/orders; gateway is depth 2 (it depends on all
# three of those, not on db-main directly) — the one node in this system
# whose presence in affected_nodes actually depends on propagation depth.

class TestDurationAffectsPropagation:
    def _experiment(self, system_id: str, duration: int) -> Experiment:
        return Experiment(
            id=f"exp-duration-{duration}",
            system_id=system_id,
            target_node="db-main",
            type="service_down",
            duration_seconds=duration,
        )

    def test_a_brief_experiment_is_contained_to_direct_dependents(self, demo_system):
        run, _ = _run(demo_system, self._experiment(demo_system.id, 10))
        assert set(run.affected_nodes) == {"auth", "catalog", "orders"}
        assert "gateway" not in run.affected_nodes

    def test_the_default_duration_cascades_fully_unchanged_from_before(self, demo_system):
        """Locks in backward compatibility: 30s must reproduce exactly the
        pre-existing unlimited-depth behavior every other test in this file
        was written against."""
        run, _ = _run(demo_system, self._experiment(demo_system.id, 30))
        assert set(run.affected_nodes) == {"auth", "catalog", "orders", "gateway"}

    def test_a_sustained_experiment_also_cascades_fully(self, demo_system):
        run, _ = _run(demo_system, self._experiment(demo_system.id, 60))
        assert set(run.affected_nodes) == {"auth", "catalog", "orders", "gateway"}

    def test_10s_30s_and_60s_produce_three_different_results(self, demo_system):
        """The exact scenario this feature exists for: three different
        configured durations against the same target must not collapse
        into the same outcome."""
        run_10, _ = _run(demo_system, self._experiment(demo_system.id, 10))
        run_30, _ = _run(demo_system, self._experiment(demo_system.id, 30))
        run_60, _ = _run(demo_system, self._experiment(demo_system.id, 60))

        # Different propagation footprint.
        assert set(run_10.affected_nodes) != set(run_30.affected_nodes)

        # Different recovery times for the target, strictly increasing.
        target_10 = next(r.recovery_time_seconds for r in run_10.recoveries if r.node_id == "db-main")
        target_30 = next(r.recovery_time_seconds for r in run_30.recoveries if r.node_id == "db-main")
        target_60 = next(r.recovery_time_seconds for r in run_60.recoveries if r.node_id == "db-main")
        assert target_10 < target_30 < target_60

    def test_same_duration_is_reproducible(self, demo_system):
        """Determinism: the same experiment parameters must always produce
        the same result, run after run."""
        run_a, _ = _run(demo_system, self._experiment(demo_system.id, 45))
        run_b, _ = _run(demo_system, self._experiment(demo_system.id, 45))
        assert run_a.affected_nodes == run_b.affected_nodes
        assert [(r.node_id, r.recovery_status, r.recovery_time_seconds) for r in run_a.recoveries] == \
               [(r.node_id, r.recovery_status, r.recovery_time_seconds) for r in run_b.recoveries]

    def test_a_sustained_failure_can_leave_a_distant_node_unrecovered(self, demo_system):
        """gateway is depth 2 from db-main — this is the real chaos-engine
        path (not a hand-built test fixture) that finally makes a 'failed'
        recovery reachable."""
        run, _ = _run(demo_system, self._experiment(demo_system.id, 60))
        gateway_recovery = next(r for r in run.recoveries if r.node_id == "gateway")
        assert gateway_recovery.recovery_status == "failed"
        assert gateway_recovery.recovery_time_seconds is None

    def test_short_experiments_never_produce_a_failed_recovery(self, demo_system):
        for duration in (10, 30):
            run, _ = _run(demo_system, self._experiment(demo_system.id, duration))
            assert all(r.recovery_status == "recovered" for r in run.recoveries)


# ── Validation errors ─────────────────────────────────────────────────────────

class TestValidation:
    def test_system_id_mismatch_raises_value_error(self, demo_system):
        bad_exp = Experiment(
            id="exp-bad-system",
            system_id="wrong-system-id",
            target_node="gateway",
            type="service_down",
            duration_seconds=10,
        )
        engine = ChaosEngine(demo_system)
        with pytest.raises(ValueError, match="system"):
            engine.run(bad_exp)

    def test_unknown_target_node_raises_value_error(self, demo_system):
        bad_exp = Experiment(
            id="exp-bad-node",
            system_id=demo_system.id,
            target_node="does-not-exist",
            type="service_down",
            duration_seconds=10,
        )
        engine = ChaosEngine(demo_system)
        with pytest.raises(ValueError, match="does not exist"):
            engine.run(bad_exp)

    def test_traffic_spike_is_accepted(self, demo_system):
        """
        'traffic_spike' is now fully implemented and must NOT raise.
        """
        exp = Experiment(
            id="exp-traffic",
            system_id=demo_system.id,
            target_node="gateway",
            type="traffic_spike",
            duration_seconds=10,
        )
        engine = ChaosEngine(demo_system)
        run, events = engine.run(exp)
        assert run.status == "completed"
        assert isinstance(events, list)


# ── Latency spike ─────────────────────────────────────────────────────────────

class TestLatencySpike:
    def test_latency_spike_is_accepted(self, demo_system, latency_spike_db_main):
        """latency_spike produces a completed run without raising."""
        run, _ = _run(demo_system, latency_spike_db_main)
        assert run.status == "completed"

    def test_latency_spike_target_is_degraded_not_failed(
        self, demo_system, latency_spike_db_main
    ):
        """
        Unlike service_down, latency_spike must NOT emit a 'failure_injected'
        event — the target becomes degraded (node_degraded), not failed.
        """
        _, events = _run(demo_system, latency_spike_db_main)
        event_types = [e.event_type for e in events]
        assert "failure_injected" not in event_types
        assert "node_degraded" in event_types

    def test_latency_spike_produces_node_degraded_events(
        self, demo_system, latency_spike_db_main
    ):
        run, events = _run(demo_system, latency_spike_db_main)
        degraded_ids = {e.node_id for e in events if e.event_type == "node_degraded"}
        # Target itself must be present.
        assert latency_spike_db_main.target_node in degraded_ids
        # All affected nodes must also have a degraded event.
        for node_id in run.affected_nodes:
            assert node_id in degraded_ids

    def test_latency_spike_affected_nodes_correct(
        self, demo_system, latency_spike_db_main
    ):
        """db-main affects same 4 nodes regardless of experiment type."""
        run, _ = _run(demo_system, latency_spike_db_main)
        assert len(run.affected_nodes) == 4
        affected_set = set(run.affected_nodes)
        assert "auth"    in affected_set
        assert "catalog" in affected_set
        assert "orders"  in affected_set
        assert "gateway" in affected_set

    def test_latency_spike_recovery_target_time_is_8_seconds(
        self, demo_system, latency_spike_db_main
    ):
        run, _ = _run(demo_system, latency_spike_db_main)
        target_recovery = next(
            r for r in run.recoveries if r.node_id == latency_spike_db_main.target_node
        )
        assert target_recovery.recovery_time_seconds == pytest.approx(8.0)

    def test_latency_spike_gateway_has_zero_affected_nodes(
        self, demo_system, latency_spike_gateway
    ):
        run, _ = _run(demo_system, latency_spike_gateway)
        assert run.affected_nodes == []

    def test_latency_spike_target_severity_is_0_8(
        self, demo_system, latency_spike_db_main
    ):
        _, events = _run(demo_system, latency_spike_db_main)
        target_events = [
            e for e in events if e.node_id == latency_spike_db_main.target_node
        ]
        assert len(target_events) == 1
        assert target_events[0].severity == pytest.approx(0.8)


# ── Resource exhaustion ───────────────────────────────────────────────────────

class TestResourceExhaustion:
    def test_resource_exhaustion_is_accepted(self, demo_system, resource_exhaustion_db_main):
        run, _ = _run(demo_system, resource_exhaustion_db_main)
        assert run.status == "completed"

    def test_resource_exhaustion_target_is_degraded(
        self, demo_system, resource_exhaustion_db_main
    ):
        """resource_exhaustion must not emit failure_injected."""
        _, events = _run(demo_system, resource_exhaustion_db_main)
        event_types = [e.event_type for e in events]
        assert "failure_injected" not in event_types
        assert "node_degraded" in event_types

    def test_resource_exhaustion_produces_node_degraded_events(
        self, demo_system, resource_exhaustion_db_main
    ):
        run, events = _run(demo_system, resource_exhaustion_db_main)
        degraded_ids = {e.node_id for e in events if e.event_type == "node_degraded"}
        assert resource_exhaustion_db_main.target_node in degraded_ids
        for node_id in run.affected_nodes:
            assert node_id in degraded_ids

    def test_resource_exhaustion_affected_nodes_correct(
        self, demo_system, resource_exhaustion_db_main
    ):
        run, _ = _run(demo_system, resource_exhaustion_db_main)
        assert len(run.affected_nodes) == 4
        affected_set = set(run.affected_nodes)
        assert "auth"    in affected_set
        assert "catalog" in affected_set
        assert "orders"  in affected_set
        assert "gateway" in affected_set

    def test_resource_exhaustion_recovery_target_time_is_12_seconds(
        self, demo_system, resource_exhaustion_db_main
    ):
        run, _ = _run(demo_system, resource_exhaustion_db_main)
        target_recovery = next(
            r for r in run.recoveries if r.node_id == resource_exhaustion_db_main.target_node
        )
        assert target_recovery.recovery_time_seconds == pytest.approx(12.0)

    def test_resource_exhaustion_target_severity_is_0_9(
        self, demo_system, resource_exhaustion_db_main
    ):
        _, events = _run(demo_system, resource_exhaustion_db_main)
        target_events = [
            e for e in events if e.node_id == resource_exhaustion_db_main.target_node
        ]
        assert len(target_events) == 1
        assert target_events[0].severity == pytest.approx(0.9)

    def test_resource_exhaustion_gateway_has_zero_affected_nodes(
        self, demo_system, resource_exhaustion_gateway
    ):
        run, _ = _run(demo_system, resource_exhaustion_gateway)
        assert run.affected_nodes == []


# ── Traffic spike ─────────────────────────────────────────────────────────────

class TestTrafficSpike:
    def test_traffic_spike_is_accepted(self, demo_system, traffic_spike_db_main):
        """traffic_spike produces a completed run without raising."""
        run, _ = _run(demo_system, traffic_spike_db_main)
        assert run.status == "completed"

    def test_traffic_spike_target_is_degraded_not_failed(
        self, demo_system, traffic_spike_db_main
    ):
        """traffic_spike must NOT emit 'failure_injected' — target is node_degraded."""
        _, events = _run(demo_system, traffic_spike_db_main)
        event_types = [e.event_type for e in events]
        assert "failure_injected" not in event_types
        assert "node_degraded" in event_types

    def test_traffic_spike_produces_node_degraded_events_for_all(
        self, demo_system, traffic_spike_db_main
    ):
        run, events = _run(demo_system, traffic_spike_db_main)
        degraded_ids = {e.node_id for e in events if e.event_type == "node_degraded"}
        assert traffic_spike_db_main.target_node in degraded_ids
        for node_id in run.affected_nodes:
            assert node_id in degraded_ids

    def test_traffic_spike_affected_nodes_correct(
        self, demo_system, traffic_spike_db_main
    ):
        """db-main affects same 4 nodes regardless of experiment type."""
        run, _ = _run(demo_system, traffic_spike_db_main)
        assert len(run.affected_nodes) == 4
        affected_set = set(run.affected_nodes)
        assert "auth"    in affected_set
        assert "catalog" in affected_set
        assert "orders"  in affected_set
        assert "gateway" in affected_set

    def test_traffic_spike_recovery_target_time_is_10_seconds(
        self, demo_system, traffic_spike_db_main
    ):
        run, _ = _run(demo_system, traffic_spike_db_main)
        target_recovery = next(
            r for r in run.recoveries if r.node_id == traffic_spike_db_main.target_node
        )
        assert target_recovery.recovery_time_seconds == pytest.approx(10.0)

    def test_traffic_spike_affected_recovery_times_start_at_7_seconds(
        self, demo_system, traffic_spike_db_main
    ):
        run, _ = _run(demo_system, traffic_spike_db_main)
        affected_recoveries = [r for r in run.recoveries if r.node_id != traffic_spike_db_main.target_node]
        assert affected_recoveries[0].recovery_time_seconds == pytest.approx(7.0)

    def test_traffic_spike_affected_recovery_times_increment_by_0_2(
        self, demo_system, traffic_spike_db_main
    ):
        run, _ = _run(demo_system, traffic_spike_db_main)
        affected_recoveries = [r for r in run.recoveries if r.node_id != traffic_spike_db_main.target_node]
        for i, recovery in enumerate(affected_recoveries):
            expected = 7.0 + i * 0.2
            assert recovery.recovery_time_seconds == pytest.approx(expected)

    def test_traffic_spike_target_severity_is_0_85(
        self, demo_system, traffic_spike_db_main
    ):
        _, events = _run(demo_system, traffic_spike_db_main)
        target_events = [
            e for e in events if e.node_id == traffic_spike_db_main.target_node
        ]
        assert len(target_events) == 1
        assert target_events[0].severity == pytest.approx(0.85)

    def test_traffic_spike_gateway_has_zero_affected_nodes(
        self, demo_system, traffic_spike_gateway
    ):
        run, _ = _run(demo_system, traffic_spike_gateway)
        assert run.affected_nodes == []

    def test_traffic_spike_run_id_is_prefixed(self, demo_system, traffic_spike_db_main):
        run, _ = _run(demo_system, traffic_spike_db_main)
        assert run.id == f"run-{traffic_spike_db_main.id}"

    def test_traffic_spike_event_id_includes_traffic(
        self, demo_system, traffic_spike_db_main
    ):
        """The primary event ID for traffic_spike contains 'traffic'."""
        _, events = _run(demo_system, traffic_spike_db_main)
        target_events = [e for e in events if e.node_id == traffic_spike_db_main.target_node]
        assert "traffic" in target_events[0].id
