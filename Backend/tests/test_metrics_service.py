"""
Unit tests for MetricsService.

Verifies the three fixed metric profiles (healthy / degraded / failed),
snapshot creation, status override application, and delta calculation.
All expected values are derived directly from the production constants in
MetricsService — nothing is guessed.

Production constants (MetricsService):
  healthy:  cpu=35.0, mem=55.0, latency=40.0, error=0.2
  degraded: cpu=70.0, mem=68.0, latency=220.0, error=4.0
  failed:   cpu=95.0, mem=90.0, latency=1000.0, error=25.0
"""

import pytest

from app.models.system import System
from app.services.metrics_service import MetricsService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def svc() -> MetricsService:
    return MetricsService()


# ── Metric profiles ───────────────────────────────────────────────────────────

class TestMetricProfiles:
    def test_healthy_cpu(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "gateway", "healthy")
        assert m.cpu_usage == pytest.approx(35.0)

    def test_healthy_memory(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "gateway", "healthy")
        assert m.memory_usage == pytest.approx(55.0)

    def test_healthy_latency(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "gateway", "healthy")
        assert m.latency_ms == pytest.approx(40.0)

    def test_healthy_error_rate(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "gateway", "healthy")
        assert m.error_rate == pytest.approx(0.2)

    def test_degraded_cpu(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "auth", "degraded")
        assert m.cpu_usage == pytest.approx(70.0)

    def test_degraded_memory(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "auth", "degraded")
        assert m.memory_usage == pytest.approx(68.0)

    def test_degraded_latency(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "auth", "degraded")
        assert m.latency_ms == pytest.approx(220.0)

    def test_degraded_error_rate(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "auth", "degraded")
        assert m.error_rate == pytest.approx(4.0)

    def test_failed_cpu(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "db-main", "failed")
        assert m.cpu_usage == pytest.approx(95.0)

    def test_failed_memory(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "db-main", "failed")
        assert m.memory_usage == pytest.approx(90.0)

    def test_failed_latency(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "db-main", "failed")
        assert m.latency_ms == pytest.approx(1000.0)

    def test_failed_error_rate(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "db-main", "failed")
        assert m.error_rate == pytest.approx(25.0)

    def test_metric_node_id_matches_requested_node(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "orders", "healthy")
        assert m.node_id == "orders"

    def test_unknown_node_raises_value_error(self, svc, demo_system):
        with pytest.raises(ValueError, match="does not exist"):
            svc.get_node_metrics(demo_system, "nonexistent-node", "healthy")


# ── Snapshots ─────────────────────────────────────────────────────────────────

class TestSnapshots:
    def test_snapshot_covers_all_nodes(self, svc, demo_system):
        snapshots = svc.create_snapshot(demo_system)
        assert len(snapshots) == len(demo_system.nodes)

    def test_snapshot_node_ids_match_system(self, svc, demo_system):
        snapshots = svc.create_snapshot(demo_system)
        snapshot_ids = {s.node_id for s in snapshots}
        system_ids   = {n.id      for n in demo_system.nodes}
        assert snapshot_ids == system_ids

    def test_snapshot_without_overrides_all_healthy(self, svc, demo_system):
        snapshots = svc.create_snapshot(demo_system)
        for snapshot in snapshots:
            assert snapshot.metrics["cpu_usage"]    == pytest.approx(35.0)
            assert snapshot.metrics["memory_usage"] == pytest.approx(55.0)
            assert snapshot.metrics["latency_ms"]   == pytest.approx(40.0)
            assert snapshot.metrics["error_rate"]   == pytest.approx(0.2)

    def test_snapshot_override_applies_failed_profile_to_target(self, svc, demo_system):
        overrides = {"db-main": "failed"}
        snapshots = svc.create_snapshot(demo_system, overrides)
        db_snapshot = next(s for s in snapshots if s.node_id == "db-main")
        assert db_snapshot.metrics["cpu_usage"]  == pytest.approx(95.0)
        assert db_snapshot.metrics["latency_ms"] == pytest.approx(1000.0)

    def test_snapshot_override_non_overridden_nodes_remain_healthy(self, svc, demo_system):
        overrides = {"db-main": "failed"}
        snapshots = svc.create_snapshot(demo_system, overrides)
        for snapshot in snapshots:
            if snapshot.node_id == "db-main":
                continue
            assert snapshot.metrics["cpu_usage"] == pytest.approx(35.0)

    def test_snapshot_contains_required_metric_keys(self, svc, demo_system):
        snapshots = svc.create_snapshot(demo_system)
        for snapshot in snapshots:
            assert "cpu_usage"    in snapshot.metrics
            assert "memory_usage" in snapshot.metrics
            assert "latency_ms"   in snapshot.metrics
            assert "error_rate"   in snapshot.metrics


# ── Comparisons ───────────────────────────────────────────────────────────────

class TestComparisons:
    def test_comparison_count_equals_node_count(self, svc, demo_system):
        before = svc.create_snapshot(demo_system)
        after  = svc.create_snapshot(demo_system)
        comps  = svc.compare_snapshots(before, after)
        assert len(comps) == len(demo_system.nodes)

    def test_healthy_to_healthy_all_deltas_are_zero(self, svc, demo_system):
        before = svc.create_snapshot(demo_system)
        after  = svc.create_snapshot(demo_system)
        comps  = svc.compare_snapshots(before, after)
        for comp in comps:
            assert comp.cpu_usage_delta    == pytest.approx(0.0)
            assert comp.memory_usage_delta == pytest.approx(0.0)
            assert comp.latency_delta_ms   == pytest.approx(0.0)
            assert comp.error_rate_delta   == pytest.approx(0.0)

    def test_healthy_to_failed_produces_correct_deltas_for_target(self, svc, demo_system):
        """
        healthy → failed deltas:
          cpu:     95.0 − 35.0  =  60.0
          memory:  90.0 − 55.0  =  35.0
          latency: 1000.0 − 40.0 = 960.0
          error:   25.0 − 0.2   =  24.8
        """
        before = svc.create_snapshot(demo_system)
        after  = svc.create_snapshot(demo_system, {"db-main": "failed"})
        comps  = svc.compare_snapshots(before, after)
        db_comp = next(c for c in comps if c.node_id == "db-main")
        assert db_comp.cpu_usage_delta    == pytest.approx(60.0)
        assert db_comp.memory_usage_delta == pytest.approx(35.0)
        assert db_comp.latency_delta_ms   == pytest.approx(960.0)
        assert db_comp.error_rate_delta   == pytest.approx(24.8)

    def test_healthy_to_degraded_produces_correct_deltas(self, svc, demo_system):
        """
        healthy → degraded deltas:
          cpu:     70.0 − 35.0  = 35.0
          memory:  68.0 − 55.0  = 13.0
          latency: 220.0 − 40.0 = 180.0
          error:   4.0  − 0.2   =  3.8
        """
        before = svc.create_snapshot(demo_system)
        after  = svc.create_snapshot(demo_system, {"auth": "degraded"})
        comps  = svc.compare_snapshots(before, after)
        auth_comp = next(c for c in comps if c.node_id == "auth")
        assert auth_comp.cpu_usage_delta    == pytest.approx(35.0)
        assert auth_comp.memory_usage_delta == pytest.approx(13.0)
        assert auth_comp.latency_delta_ms   == pytest.approx(180.0)
        assert auth_comp.error_rate_delta   == pytest.approx(3.8)

    def test_comparison_node_ids_match_system(self, svc, demo_system):
        before = svc.create_snapshot(demo_system)
        after  = svc.create_snapshot(demo_system)
        comps  = svc.compare_snapshots(before, after)
        comp_ids   = {c.node_id for c in comps}
        system_ids = {n.id      for n in demo_system.nodes}
        assert comp_ids == system_ids


# ── Latency spike metric profile ──────────────────────────────────────────────

class TestLatencySpikeProfile:
    def test_latency_spike_target_has_high_latency(self, svc, demo_system):
        """Target node under latency_spike has severely elevated latency (800ms)."""
        m = svc.get_node_metrics(demo_system, "db-main", "degraded", "latency_spike")
        assert m.latency_ms == pytest.approx(800.0)

    def test_latency_spike_target_cpu_is_near_normal(self, svc, demo_system):
        """CPU should only be slightly elevated (40.0) for a latency spike — not high."""
        m = svc.get_node_metrics(demo_system, "db-main", "degraded", "latency_spike")
        assert m.cpu_usage == pytest.approx(40.0)

    def test_latency_spike_target_memory_is_near_normal(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "db-main", "degraded", "latency_spike")
        assert m.memory_usage == pytest.approx(58.0)

    def test_latency_spike_target_error_rate(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "db-main", "degraded", "latency_spike")
        assert m.error_rate == pytest.approx(3.0)

    def test_latency_spike_degraded_has_elevated_latency(self, svc, demo_system):
        """Downstream (degraded) node under latency_spike has latency 350ms."""
        m = svc.get_node_metrics(demo_system, "auth", "degraded", "latency_spike")
        assert m.latency_ms == pytest.approx(800.0)

    def test_latency_spike_snapshot_target_has_high_latency(self, svc, demo_system):
        snap = svc.create_snapshot(demo_system, {"db-main": "degraded"}, "latency_spike")
        db_snap = next(s for s in snap if s.node_id == "db-main")
        assert db_snap.metrics["latency_ms"] == pytest.approx(800.0)

    def test_latency_spike_snapshot_non_target_nodes_remain_healthy(self, svc, demo_system):
        snap = svc.create_snapshot(demo_system, {"db-main": "degraded"}, "latency_spike")
        for s in snap:
            if s.node_id == "db-main":
                continue
            assert s.metrics["cpu_usage"] == pytest.approx(35.0)


# ── Resource exhaustion metric profile ────────────────────────────────────────

class TestResourceExhaustionProfile:
    def test_resource_exhaustion_target_has_high_cpu(self, svc, demo_system):
        """Target node under resource_exhaustion has critically high CPU (92.0)."""
        m = svc.get_node_metrics(demo_system, "db-main", "degraded", "resource_exhaustion")
        assert m.cpu_usage == pytest.approx(92.0)

    def test_resource_exhaustion_target_has_high_memory(self, svc, demo_system):
        """Target node under resource_exhaustion has critically high memory (88.0)."""
        m = svc.get_node_metrics(demo_system, "db-main", "degraded", "resource_exhaustion")
        assert m.memory_usage == pytest.approx(88.0)

    def test_resource_exhaustion_target_error_rate(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "db-main", "degraded", "resource_exhaustion")
        assert m.error_rate == pytest.approx(8.0)

    def test_resource_exhaustion_target_latency(self, svc, demo_system):
        m = svc.get_node_metrics(demo_system, "db-main", "degraded", "resource_exhaustion")
        assert m.latency_ms == pytest.approx(180.0)

    def test_resource_exhaustion_differs_from_latency_spike(self, svc, demo_system):
        """The two new experiment types must produce distinct metric profiles."""
        lat = svc.get_node_metrics(demo_system, "db-main", "degraded", "latency_spike")
        res = svc.get_node_metrics(demo_system, "db-main", "degraded", "resource_exhaustion")
        # Latency spike has much higher latency
        assert lat.latency_ms > res.latency_ms
        # Resource exhaustion has much higher CPU
        assert res.cpu_usage > lat.cpu_usage
        # Resource exhaustion has much higher memory
        assert res.memory_usage > lat.memory_usage

    def test_resource_exhaustion_snapshot_target_has_high_cpu(self, svc, demo_system):
        snap = svc.create_snapshot(demo_system, {"db-main": "degraded"}, "resource_exhaustion")
        db_snap = next(s for s in snap if s.node_id == "db-main")
        assert db_snap.metrics["cpu_usage"] == pytest.approx(92.0)

    def test_service_down_degraded_profile_unchanged(self, svc, demo_system):
        """The existing service_down degraded profile must not be affected."""
        m = svc.get_node_metrics(demo_system, "auth", "degraded", "service_down")
        assert m.cpu_usage    == pytest.approx(70.0)
        assert m.memory_usage == pytest.approx(68.0)
        assert m.latency_ms   == pytest.approx(220.0)
        assert m.error_rate   == pytest.approx(4.0)
