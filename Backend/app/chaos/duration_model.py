"""
Deterministic mapping from an experiment's configured duration to real
consequences in the simulation model.

Before this module existed, `duration_seconds` was accepted by the API,
stored, and displayed — but never once read by anything that computed a
result. Every formula here is a pure function of `duration_seconds` (and,
where relevant, topological distance from the target) — same inputs always
produce the same outputs, so an experiment is exactly as reproducible as it
was before.

Every formula is anchored so that duration_seconds == DEFAULT_DURATION
reproduces exactly the fixed values the chaos engine and metrics service
used before this module existed — the platform's own default duration
(30s, see Frontend/src/components/experiment/ExperimentModal.tsx) is the
baseline every existing test and demo expectation was written against.
"""

DEFAULT_DURATION = 30

# A brief failure (<= 15s) is treated as contained — it never gets the
# chance to cascade past its direct dependents. Anything longer is allowed
# to cascade fully (today's unlimited-depth behavior), because a sustained
# outage genuinely has more time to ripple through a dependency chain.
_CONTAINED_DURATION_THRESHOLD = 15
_CONTAINED_DEPTH = 1

# A node more than one hop from the target can fail to fully recover only
# once the failure has run long enough to matter — short of that, every
# affected node is assumed to bounce back within the experiment window.
_RECOVERY_FAILURE_DURATION_THRESHOLD = 60
_RECOVERY_FAILURE_MIN_DEPTH = 2

# Recovery time and metric severity both scale linearly with duration
# relative to the baseline, clamped so pathologically short/long durations
# can't produce a degenerate (near-zero or absurd) result.
_RECOVERY_FACTOR_MIN = 0.4
_RECOVERY_FACTOR_MAX = 2.5
_SEVERITY_FACTOR_MIN = 0.5
_SEVERITY_FACTOR_MAX = 1.8


def propagation_depth(duration_seconds: int) -> int | None:
    """
    How many hops a failure is allowed to cascade through the dependency
    graph. `None` means unlimited (cascades until it runs out of
    dependents) — the behavior every duration used before this module
    existed.
    """
    if duration_seconds <= _CONTAINED_DURATION_THRESHOLD:
        return _CONTAINED_DEPTH
    return None


def recovery_time_factor(duration_seconds: int) -> float:
    """
    Multiplier applied to the base recovery time for an experiment type.
    1.0 at the default duration (reproduces today's exact constants);
    below 1.0 for shorter experiments (recovering from a brief outage is
    faster), above 1.0 for longer ones.
    """
    factor = duration_seconds / DEFAULT_DURATION
    return max(_RECOVERY_FACTOR_MIN, min(factor, _RECOVERY_FACTOR_MAX))


def severity_factor(duration_seconds: int) -> float:
    """
    Multiplier applied to how far a degraded/failed node's metrics move
    away from their healthy baseline. 1.0 at the default duration
    (reproduces today's exact metric profiles); a sustained failure pushes
    metrics further from healthy, a brief one less far.
    """
    factor = 0.6 + 0.4 * (duration_seconds / DEFAULT_DURATION)
    return max(_SEVERITY_FACTOR_MIN, min(factor, _SEVERITY_FACTOR_MAX))


def recovery_fails_at_depth(duration_seconds: int, depth: int) -> bool:
    """
    Whether a node this many hops from the target should fail to recover
    within the experiment window. Deterministic and topology-aware: the
    same (duration, depth) pair always gives the same answer — this is
    what makes RecoveryAnalysis.failed_recoveries (and the
    "recovery_validation" follow-up recommendation it feeds) reachable
    from a real chaos run instead of only from hand-built test fixtures.
    """
    return (
        duration_seconds >= _RECOVERY_FAILURE_DURATION_THRESHOLD
        and depth >= _RECOVERY_FAILURE_MIN_DEPTH
    )
