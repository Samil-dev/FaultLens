from datetime import datetime, timezone

from app.chaos import duration_model
from app.graph.dependency_graph import DependencyGraph
from app.models.experiment import Experiment
from app.models.recovery import Recovery
from app.models.simulation_event import SimulationEvent
from app.models.simulation_run import SimulationRun
from app.models.system import System

class ChaosEngine:
    """
    Core simulation engine for FaultLens.

    The engine performs simulated chaos experiments
    without affecting real infrastructure.

    Supported experiment types:
      - service_down:         target → failed,   affected → degraded
      - latency_spike:        target → degraded, affected → degraded
      - resource_exhaustion:  target → degraded, affected → degraded
      - traffic_spike:        target → degraded, affected → degraded

    `experiment.duration_seconds` has real, deterministic consequences (see
    app.chaos.duration_model): how far the failure is allowed to cascade,
    how long recovery takes, and whether a node far enough from the target
    fails to recover within the experiment window at all. Every rule is
    anchored at duration_model.DEFAULT_DURATION (30s), so a 30-second
    experiment reproduces exactly the fixed outcome this engine always
    produced before duration became a real parameter.
    """

    def __init__(self, system: System):
        self.system = system
        self.graph = DependencyGraph(system)

    def run(
        self,
        experiment: Experiment
    ) -> tuple[SimulationRun, list[SimulationEvent]]:
        """
        Executes a simulated chaos experiment.
        """

        # Ensure the experiment targets this system.
        if experiment.system_id != self.system.id:
            raise ValueError(
                f"Experiment targets system '{experiment.system_id}'."
                f"but engine contains system '{self.system.id}'"
            )

        # Ensure the target node exists.
        node_ids = {node.id for node in self.system.nodes}

        if experiment.target_node not in node_ids:
            raise ValueError(
                f"Target node '{experiment.target_node}'"
                f" does not exist in the system"
            )

        # Dispatch to the correct handler.
        if experiment.type == "service_down":
            return self._run_service_down(experiment)

        if experiment.type == "latency_spike":
            return self._run_latency_spike(experiment)

        if experiment.type == "resource_exhaustion":
            return self._run_resource_exhaustion(experiment)

        if experiment.type == "traffic_spike":
            return self._run_traffic_spike(experiment)

        raise ValueError(
            f"Experiment type '{experiment.type}' is not supported"
        )

    # ── Shared duration-aware helpers ───────────────────────────────────────────

    def _affected_nodes(self, target_node: str, duration_seconds: int) -> list[str]:
        """
        Real, topology-driven propagation, capped by how long the failure
        ran — a brief failure is contained to direct dependents; a
        sustained one cascades through the full dependency chain.
        """
        depth_limit = duration_model.propagation_depth(duration_seconds)
        return self.graph.get_affected_nodes(target_node, max_depth=depth_limit)

    def _build_recoveries(
        self,
        target_node: str,
        affected_nodes: list[str],
        duration_seconds: int,
        target_base_seconds: float,
        affected_base_seconds: float,
        affected_step_seconds: float,
    ) -> list[Recovery]:
        """
        Builds the recovery record for the target plus every affected node.

        Recovery time scales with how long the failure ran (recovering from
        a brief outage is faster than from a sustained one). A node more
        than one hop from the target can fail to recover outright once the
        failure has run long enough — deterministic and topology-aware, see
        duration_model.recovery_fails_at_depth().
        """
        factor = duration_model.recovery_time_factor(duration_seconds)
        node_depths = self.graph.get_affected_node_depths(target_node)

        recoveries = [
            Recovery(
                node_id=target_node,
                recovery_status="recovered",
                recovery_time_seconds=round(target_base_seconds * factor, 2),
            )
        ]

        for index, node_id in enumerate(affected_nodes):
            depth = node_depths.get(node_id, 1)
            if duration_model.recovery_fails_at_depth(duration_seconds, depth):
                recoveries.append(
                    Recovery(
                        node_id=node_id,
                        recovery_status="failed",
                        recovery_time_seconds=None,
                    )
                )
            else:
                base = affected_base_seconds + (index * affected_step_seconds)
                recoveries.append(
                    Recovery(
                        node_id=node_id,
                        recovery_status="recovered",
                        recovery_time_seconds=round(base * factor, 2),
                    )
                )

        return recoveries

    # ── Private handlers ──────────────────────────────────────────────────────

    def _run_service_down(
        self,
        experiment: Experiment,
    ) -> tuple[SimulationRun, list[SimulationEvent]]:
        """
        Brings the target node completely offline (status: failed).
        Affected downstream nodes become degraded.
        """
        now = datetime.now(timezone.utc)

        affected_nodes = self._affected_nodes(experiment.target_node, experiment.duration_seconds)

        events: list[SimulationEvent] = []

        # Target node: failure_injected at full severity.
        events.append(
            SimulationEvent(
                id=f"event-{experiment.id}-failure",
                run_id=f"run-{experiment.id}",
                node_id=experiment.target_node,
                event_type="failure_injected",
                severity=1.0,
                timestamp=now,
            )
        )

        # Affected nodes become degraded with decreasing severity.
        for index, node_id in enumerate(affected_nodes):
            events.append(
                SimulationEvent(
                    id=f"event-{experiment.id}-{index}",
                    run_id=f"run-{experiment.id}",
                    node_id=node_id,
                    event_type="node_degraded",
                    severity=max(0.1, 1.0 - ((index + 1) * 0.2)),
                    timestamp=now,
                )
            )

        recoveries = self._build_recoveries(
            experiment.target_node,
            affected_nodes,
            experiment.duration_seconds,
            target_base_seconds=15.0,
            affected_base_seconds=8.0,
            affected_step_seconds=0.2,
        )

        run = SimulationRun(
            id=f"run-{experiment.id}",
            experiment_id=experiment.id,
            type=experiment.type,
            target_node=experiment.target_node,
            status="completed",
            started_at=now,
            finished_at=now,
            affected_nodes=affected_nodes,
            recoveries=recoveries,
        )

        return run, events

    def _run_latency_spike(
        self,
        experiment: Experiment,
    ) -> tuple[SimulationRun, list[SimulationEvent]]:
        """
        Injects high latency into the target node (status: degraded).
        Affected downstream nodes also become degraded.
        """
        now = datetime.now(timezone.utc)

        affected_nodes = self._affected_nodes(experiment.target_node, experiment.duration_seconds)

        events: list[SimulationEvent] = []

        # Target node: node_degraded at severity 0.8.
        events.append(
            SimulationEvent(
                id=f"event-{experiment.id}-latency",
                run_id=f"run-{experiment.id}",
                node_id=experiment.target_node,
                event_type="node_degraded",
                severity=0.8,
                timestamp=now,
            )
        )

        # Affected nodes also degraded.
        for index, node_id in enumerate(affected_nodes):
            events.append(
                SimulationEvent(
                    id=f"event-{experiment.id}-{index}",
                    run_id=f"run-{experiment.id}",
                    node_id=node_id,
                    event_type="node_degraded",
                    severity=max(0.1, 0.8 - ((index + 1) * 0.15)),
                    timestamp=now,
                )
            )

        recoveries = self._build_recoveries(
            experiment.target_node,
            affected_nodes,
            experiment.duration_seconds,
            target_base_seconds=8.0,
            affected_base_seconds=5.0,
            affected_step_seconds=0.2,
        )

        run = SimulationRun(
            id=f"run-{experiment.id}",
            experiment_id=experiment.id,
            type=experiment.type,
            target_node=experiment.target_node,
            status="completed",
            started_at=now,
            finished_at=now,
            affected_nodes=affected_nodes,
            recoveries=recoveries,
        )

        return run, events

    def _run_traffic_spike(
        self,
        experiment: Experiment,
    ) -> tuple[SimulationRun, list[SimulationEvent]]:
        """
        Simulates a traffic spike against the target node (status: degraded).
        High error rate and elevated latency are the primary signatures.
        Affected downstream nodes also become degraded.
        """
        now = datetime.now(timezone.utc)

        affected_nodes = self._affected_nodes(experiment.target_node, experiment.duration_seconds)

        events: list[SimulationEvent] = []

        # Target node: node_degraded at severity 0.85.
        events.append(
            SimulationEvent(
                id=f"event-{experiment.id}-traffic",
                run_id=f"run-{experiment.id}",
                node_id=experiment.target_node,
                event_type="node_degraded",
                severity=0.85,
                timestamp=now,
            )
        )

        # Affected nodes also degraded.
        for index, node_id in enumerate(affected_nodes):
            events.append(
                SimulationEvent(
                    id=f"event-{experiment.id}-{index}",
                    run_id=f"run-{experiment.id}",
                    node_id=node_id,
                    event_type="node_degraded",
                    severity=max(0.1, 0.85 - ((index + 1) * 0.15)),
                    timestamp=now,
                )
            )

        recoveries = self._build_recoveries(
            experiment.target_node,
            affected_nodes,
            experiment.duration_seconds,
            target_base_seconds=10.0,
            affected_base_seconds=7.0,
            affected_step_seconds=0.2,
        )

        run = SimulationRun(
            id=f"run-{experiment.id}",
            experiment_id=experiment.id,
            type=experiment.type,
            target_node=experiment.target_node,
            status="completed",
            started_at=now,
            finished_at=now,
            affected_nodes=affected_nodes,
            recoveries=recoveries,
        )

        return run, events

    def _run_resource_exhaustion(
        self,
        experiment: Experiment,
    ) -> tuple[SimulationRun, list[SimulationEvent]]:
        """
        Saturates CPU/memory on the target node (status: degraded).
        Affected downstream nodes also become degraded.
        """
        now = datetime.now(timezone.utc)

        affected_nodes = self._affected_nodes(experiment.target_node, experiment.duration_seconds)

        events: list[SimulationEvent] = []

        # Target node: node_degraded at severity 0.9.
        events.append(
            SimulationEvent(
                id=f"event-{experiment.id}-resource",
                run_id=f"run-{experiment.id}",
                node_id=experiment.target_node,
                event_type="node_degraded",
                severity=0.9,
                timestamp=now,
            )
        )

        # Affected nodes also degraded.
        for index, node_id in enumerate(affected_nodes):
            events.append(
                SimulationEvent(
                    id=f"event-{experiment.id}-{index}",
                    run_id=f"run-{experiment.id}",
                    node_id=node_id,
                    event_type="node_degraded",
                    severity=max(0.1, 0.9 - ((index + 1) * 0.15)),
                    timestamp=now,
                )
            )

        recoveries = self._build_recoveries(
            experiment.target_node,
            affected_nodes,
            experiment.duration_seconds,
            target_base_seconds=12.0,
            affected_base_seconds=6.0,
            affected_step_seconds=0.2,
        )

        run = SimulationRun(
            id=f"run-{experiment.id}",
            experiment_id=experiment.id,
            type=experiment.type,
            target_node=experiment.target_node,
            status="completed",
            started_at=now,
            finished_at=now,
            affected_nodes=affected_nodes,
            recoveries=recoveries,
        )

        return run, events
