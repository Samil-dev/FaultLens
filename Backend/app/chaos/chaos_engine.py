from datetime import datetime, timezone

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

        affected_nodes = self.graph.get_affected_nodes(experiment.target_node)

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

        recoveries: list[Recovery] = [
            Recovery(
                node_id=experiment.target_node,
                recovery_status="recovered",
                recovery_time_seconds=15.0,
            )
        ]

        for index, node_id in enumerate(affected_nodes):
            recoveries.append(
                Recovery(
                    node_id=node_id,
                    recovery_status="recovered",
                    recovery_time_seconds=8.0 + (index * 0.2),
                )
            )

        run = SimulationRun(
            id=f"run-{experiment.id}",
            experiment_id=experiment.id,
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

        affected_nodes = self.graph.get_affected_nodes(experiment.target_node)

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

        recoveries: list[Recovery] = [
            Recovery(
                node_id=experiment.target_node,
                recovery_status="recovered",
                recovery_time_seconds=8.0,
            )
        ]

        for index, node_id in enumerate(affected_nodes):
            recoveries.append(
                Recovery(
                    node_id=node_id,
                    recovery_status="recovered",
                    recovery_time_seconds=5.0 + (index * 0.2),
                )
            )

        run = SimulationRun(
            id=f"run-{experiment.id}",
            experiment_id=experiment.id,
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

        affected_nodes = self.graph.get_affected_nodes(experiment.target_node)

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

        recoveries: list[Recovery] = [
            Recovery(
                node_id=experiment.target_node,
                recovery_status="recovered",
                recovery_time_seconds=10.0,
            )
        ]

        for index, node_id in enumerate(affected_nodes):
            recoveries.append(
                Recovery(
                    node_id=node_id,
                    recovery_status="recovered",
                    recovery_time_seconds=7.0 + (index * 0.2),
                )
            )

        run = SimulationRun(
            id=f"run-{experiment.id}",
            experiment_id=experiment.id,
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

        affected_nodes = self.graph.get_affected_nodes(experiment.target_node)

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

        recoveries: list[Recovery] = [
            Recovery(
                node_id=experiment.target_node,
                recovery_status="recovered",
                recovery_time_seconds=12.0,
            )
        ]

        for index, node_id in enumerate(affected_nodes):
            recoveries.append(
                Recovery(
                    node_id=node_id,
                    recovery_status="recovered",
                    recovery_time_seconds=6.0 + (index * 0.2),
                )
            )

        run = SimulationRun(
            id=f"run-{experiment.id}",
            experiment_id=experiment.id,
            status="completed",
            started_at=now,
            finished_at=now,
            affected_nodes=affected_nodes,
            recoveries=recoveries,
        )

        return run, events
