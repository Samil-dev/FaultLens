"""
Unit tests for app/chaos/duration_model.py — the pure functions that give
experiment duration real, deterministic consequences.
"""

from app.chaos import duration_model


class TestPropagationDepth:
    def test_brief_experiments_are_contained_to_direct_dependents(self):
        assert duration_model.propagation_depth(10) == 1
        assert duration_model.propagation_depth(15) == 1

    def test_longer_experiments_cascade_without_a_depth_limit(self):
        assert duration_model.propagation_depth(16) is None
        assert duration_model.propagation_depth(30) is None
        assert duration_model.propagation_depth(60) is None
        assert duration_model.propagation_depth(300) is None


class TestRecoveryTimeFactor:
    def test_default_duration_is_the_unscaled_baseline(self):
        assert duration_model.recovery_time_factor(duration_model.DEFAULT_DURATION) == 1.0

    def test_shorter_duration_recovers_faster(self):
        assert duration_model.recovery_time_factor(10) < 1.0

    def test_longer_duration_recovers_slower(self):
        assert duration_model.recovery_time_factor(60) > 1.0

    def test_factor_is_monotonic_in_duration(self):
        f10 = duration_model.recovery_time_factor(10)
        f30 = duration_model.recovery_time_factor(30)
        f60 = duration_model.recovery_time_factor(60)
        assert f10 < f30 < f60

    def test_extreme_durations_are_clamped_not_degenerate(self):
        assert duration_model.recovery_time_factor(1) > 0
        assert duration_model.recovery_time_factor(100_000) < 100


class TestSeverityFactor:
    def test_default_duration_is_the_unscaled_baseline(self):
        assert duration_model.severity_factor(duration_model.DEFAULT_DURATION) == 1.0

    def test_factor_is_monotonic_in_duration(self):
        f10 = duration_model.severity_factor(10)
        f30 = duration_model.severity_factor(30)
        f60 = duration_model.severity_factor(60)
        assert f10 < f30 < f60

    def test_extreme_durations_are_clamped_not_degenerate(self):
        assert duration_model.severity_factor(1) > 0
        assert duration_model.severity_factor(100_000) < 100


class TestRecoveryFailsAtDepth:
    def test_short_experiments_never_fail_a_recovery_regardless_of_depth(self):
        assert duration_model.recovery_fails_at_depth(10, depth=1) is False
        assert duration_model.recovery_fails_at_depth(10, depth=5) is False

    def test_default_duration_never_fails_a_recovery(self):
        """The platform's own default (30s) must reproduce today's
        always-recovers behavior — this is the backward-compatibility
        anchor every existing test was written against."""
        for depth in range(1, 6):
            assert duration_model.recovery_fails_at_depth(duration_model.DEFAULT_DURATION, depth) is False

    def test_direct_dependents_never_fail_regardless_of_duration(self):
        """Depth 1 (a direct dependent) is always assumed to recover within
        the experiment window — only nodes further away can fail."""
        assert duration_model.recovery_fails_at_depth(60, depth=1) is False
        assert duration_model.recovery_fails_at_depth(600, depth=1) is False

    def test_sustained_failure_can_fail_a_distant_node(self):
        assert duration_model.recovery_fails_at_depth(60, depth=2) is True
        assert duration_model.recovery_fails_at_depth(60, depth=3) is True

    def test_result_is_a_pure_function_of_its_inputs(self):
        """Same (duration, depth) must always produce the same answer —
        this is what keeps a chaos run reproducible/deterministic."""
        results = {duration_model.recovery_fails_at_depth(60, 2) for _ in range(20)}
        assert results == {True}
