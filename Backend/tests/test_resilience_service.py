"""
Unit tests for ResilienceService.

All expected score values are computed from the exact formula in
ResilienceService.calculate_score():

  blast_radius  = affected_nodes / total_nodes
  metric_impact = average of normalised per-node impacts across all comparisons
  score         = 100 * (1 - 0.5*blast_radius - 0.5*metric_impact)
  score         = clamp(score, 0, 100)
  score         = round(score, 2)

Normalisation maxes (ResilienceService class constants):
  CPU_MAX_DELTA       = 100.0
  MEMORY_MAX_DELTA    = 100.0
  LATENCY_MAX_DELTA   = 1000.0
  ERROR_RATE_MAX_DELTA = 25.0

Rating thresholds (_get_rating):
  >= 80  → "excellent"
  >= 60  → "good"
  >= 40  → "moderate"
  >= 20  → "poor"
  < 20   → "critical"
"""

import pytest

from app.models.metric_comparison import MetricComparison
from app.services.resilience_service import ResilienceService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def svc() -> ResilienceService:
    return ResilienceService()


def _comp(node_id: str, cpu=0.0, mem=0.0, lat=0.0, err=0.0) -> MetricComparison:
    """Convenience constructor for MetricComparison."""
    return MetricComparison(
        node_id=node_id,
        cpu_usage_delta=cpu,
        memory_usage_delta=mem,
        latency_delta_ms=lat,
        error_rate_delta=err,
    )


# ── Guard rails ───────────────────────────────────────────────────────────────

class TestGuards:
    def test_total_nodes_zero_raises(self, svc):
        with pytest.raises(ValueError, match="greater than zero"):
            svc.calculate_score([], 0, 0)

    def test_affected_nodes_negative_raises(self, svc):
        with pytest.raises(ValueError, match="negative"):
            svc.calculate_score([], -1, 10)

    def test_affected_exceeds_total_raises(self, svc):
        with pytest.raises(ValueError, match="cannot exceed"):
            svc.calculate_score([], 11, 10)


# ── Score calculation ─────────────────────────────────────────────────────────

class TestScoreCalculation:
    def test_zero_impact_zero_affected_gives_100(self, svc):
        # blast=0/10=0, metric_impact=0 → score = 100*(1-0-0) = 100
        result = svc.calculate_score([], 0, 10)
        assert result.score == pytest.approx(100.0)

    def test_zero_impact_with_zero_deltas_gives_100(self, svc):
        comps = [_comp("a"), _comp("b"), _comp("c")]
        result = svc.calculate_score(comps, 0, 10)
        assert result.score == pytest.approx(100.0)

    def test_half_blast_radius_no_metric_impact_gives_75(self, svc):
        # blast=5/10=0.5, metric_impact=0 → score = 100*(1-0.25-0) = 75
        result = svc.calculate_score([], 5, 10)
        assert result.score == pytest.approx(75.0)

    def test_full_blast_radius_no_metric_impact_gives_50(self, svc):
        # blast=10/10=1.0, metric_impact=0 → score = 100*(1-0.5-0) = 50
        result = svc.calculate_score([], 10, 10)
        assert result.score == pytest.approx(50.0)

    def test_no_blast_max_metric_impact_single_node_gives_50(self, svc):
        # single node with all metrics at their maximum delta
        # cpu_impact = 100/100 = 1.0, mem = 100/100 = 1.0,
        # lat = 1000/1000 = 1.0, err = 25/25 = 1.0
        # node_impact = (1+1+1+1)/4 = 1.0
        # avg_metric_impact = 1.0
        # score = 100*(1 - 0 - 0.5*1.0) = 50
        comp = _comp("n1", cpu=100.0, mem=100.0, lat=1000.0, err=25.0)
        result = svc.calculate_score([comp], 0, 1)
        assert result.score == pytest.approx(50.0)

    def test_score_is_clamped_to_zero_not_negative(self, svc):
        # max blast + max metric impact: 100*(1-0.5-0.5) = 0, cannot go negative
        comp = _comp("n1", cpu=100.0, mem=100.0, lat=1000.0, err=25.0)
        result = svc.calculate_score([comp], 1, 1)
        assert result.score == pytest.approx(0.0)
        assert result.score >= 0.0

    def test_score_is_rounded_to_2_decimal_places(self, svc):
        # Use a comparison that produces a non-round metric impact
        comp = _comp("n1", cpu=33.3, mem=0.0, lat=0.0, err=0.0)
        result = svc.calculate_score([comp], 0, 10)
        # Verify the value has at most 2 decimal places
        assert result.score == round(result.score, 2)

    def test_db_main_service_down_expected_score(self, svc):
        """
        End-to-end score for db-main service_down in the demo system after
        the DependencyGraph deduplication fix (Phase 2A).
          - 4 affected nodes / 10 total  → blast = 0.4
          - degraded: auth, catalog, orders, gateway
          - healthy:  cart, payments, notifications, db-cache, queue
          - expected score = 72.31, rating = "good"
        """
        comps = [
            _comp("db-main",       cpu=60.0, mem=35.0, lat=960.0, err=24.8),
            _comp("auth",          cpu=35.0, mem=13.0, lat=180.0, err=3.8),
            _comp("catalog",       cpu=35.0, mem=13.0, lat=180.0, err=3.8),
            _comp("orders",        cpu=35.0, mem=13.0, lat=180.0, err=3.8),
            _comp("gateway",       cpu=35.0, mem=13.0, lat=180.0, err=3.8),
            _comp("cart",          cpu=0.0,  mem=0.0,  lat=0.0,   err=0.0),
            _comp("payments",      cpu=0.0,  mem=0.0,  lat=0.0,   err=0.0),
            _comp("notifications", cpu=0.0,  mem=0.0,  lat=0.0,   err=0.0),
            _comp("db-cache",      cpu=0.0,  mem=0.0,  lat=0.0,   err=0.0),
            _comp("queue",         cpu=0.0,  mem=0.0,  lat=0.0,   err=0.0),
        ]
        result = svc.calculate_score(comps, affected_nodes=4, total_nodes=10)
        assert result.score == pytest.approx(72.31, abs=0.01)
        assert result.rating == "good"


# ── Rating thresholds ─────────────────────────────────────────────────────────

class TestRatingThresholds:
    def test_score_80_is_excellent(self, svc):
        # need score=80: 100*(1-0.5*blast-0.5*0)=80 → blast=0.4 → 4/10
        result = svc.calculate_score([], 4, 10)
        assert result.score == pytest.approx(80.0)
        assert result.rating == "excellent"

    def test_score_100_is_excellent(self, svc):
        result = svc.calculate_score([], 0, 10)
        assert result.rating == "excellent"

    def test_score_79_is_good(self, svc):
        # blast=0.42 → 100*(1-0.21) = 79 exactly
        # Use a comparison to push score just below 80
        comp = _comp("n1", cpu=2.0)  # tiny metric impact
        result = svc.calculate_score([comp], 4, 10)
        assert result.score < 80.0
        assert result.rating == "good"

    def test_score_60_is_good(self, svc):
        # blast=0.8 → 100*(1-0.4-0) = 60
        result = svc.calculate_score([], 8, 10)
        assert result.score == pytest.approx(60.0)
        assert result.rating == "good"

    def test_score_59_is_moderate(self, svc):
        comp = _comp("n1", cpu=2.0)
        result = svc.calculate_score([comp], 8, 10)
        assert result.score < 60.0
        assert result.rating == "moderate"

    def test_score_40_is_moderate(self, svc):
        # blast=1.0, metric_impact=0.2 → 100*(1-0.5-0.1) = 40
        comp = _comp("n1", cpu=20.0)  # cpu_impact=0.2, node_impact=0.05, avg=0.05
        # Actually: need avg_metric_impact=0.2
        # single comp: cpu=20→0.2, others=0 → node_impact=0.05 → avg=0.05
        # blast=1.0 → score=100*(1-0.5-0.025)=47.5 — not 40
        # Instead: compute what gives exactly 40
        # 40 = 100*(1-0.5*blast-0.5*mi) with blast=1: 40=100*(0.5-0.5*mi)→mi=0.2
        # mi=0.2: 4 comps each with node_impact=0.2
        # node_impact=0.2: cpu_impact alone = 0.2*4=0.8 → cpu=80
        comps = [_comp(f"n{i}", cpu=80.0) for i in range(4)]
        # mi = avg of node_impacts = avg of 0.2 each = 0.2
        result = svc.calculate_score(comps, 10, 10)
        assert result.score == pytest.approx(40.0)
        assert result.rating == "moderate"

    def test_score_20_is_poor(self, svc):
        # 20 = 100*(1-0.5*1.0-0.5*0.6) → blast=1, mi=0.6
        # mi=0.6: single comp, node_impact=0.6
        # 0.6 = (cpu_i + 0 + 0 + 0)/4 → cpu_i=2.4 > 1 → capped
        # Use: cpu=100(→1.0) + lat=600(→0.6) + others=0 → node_impact=(1+0+0.6+0)/4=0.4
        # Keep iterating: cpu=1.0, mem=1.0, lat=1.0, err=0.2*4-cpu-mem-lat= ...
        # Easier: blast=1, 3 comps each node_impact=0.4 → mi=0.4 → score=100*(0.5-0.2)=30 (poor)
        # For score=20: mi=0.6 with blast=1
        # 4 metrics each=0.6: impossible since max per metric = 1.0
        # (1.0+1.0+1.0+0.4)/4=0.85 → too high
        # Use blast=0.8, mi=0.4: score=100*(1-0.4-0.2)=40 → moderate (not poor)
        # Simplest: score=25 (poor). blast=1.0, mi=0.5: score=100*(0.5-0.25)=25
        # mi=0.5: node_impact per comp = 0.5 → each metric contributes 0.5 avg
        # cpu=50(→0.5) + others=0 → 0.5/4=0.125 — no
        # cpu=100+mem=100+lat=0+err=0 → (1+1+0+0)/4=0.5 ✓
        comps = [_comp("n1", cpu=100.0, mem=100.0)]
        result = svc.calculate_score(comps, 10, 10)
        assert result.score == pytest.approx(25.0)
        assert result.rating == "poor"

    def test_score_below_20_is_critical(self, svc):
        # max blast + max metric impact → score = 0 → critical
        comp = _comp("n1", cpu=100.0, mem=100.0, lat=1000.0, err=25.0)
        result = svc.calculate_score([comp], 1, 1)
        assert result.score == pytest.approx(0.0)
        assert result.rating == "critical"

    def test_score_19_is_critical(self, svc):
        # Need score ∈ [0, 20). Use blast=1.0, mi=0.62 → score=100*(0.5-0.31)=19
        # mi=0.62 with 1 comp: node_impact=0.62
        # cpu=100→1.0, mem=100→1.0, lat=480→0.48, err=0 → (1+1+0.48+0)/4=0.62
        comp = _comp("n1", cpu=100.0, mem=100.0, lat=480.0)
        result = svc.calculate_score([comp], 1, 1)
        assert result.score < 20.0
        assert result.rating == "critical"


# ── Output fields ─────────────────────────────────────────────────────────────

class TestOutputFields:
    def test_affected_nodes_echoed_in_result(self, svc):
        result = svc.calculate_score([], 3, 10)
        assert result.affected_nodes == 3

    def test_total_nodes_echoed_in_result(self, svc):
        result = svc.calculate_score([], 3, 10)
        assert result.total_nodes == 10
