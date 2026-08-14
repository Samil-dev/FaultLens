from datetime import datetime, timezone

from app.graph.dependency_graph import DependencyGraph
from app.models.experiment import Experiment
from app.models.recovery import Recovery
from app.models.simulation_event import SimulationEvent
from app.models.simulation_run import SimulationRun
from app.models.system import System

class ChaosEngine:
    """
    Core simulation engine for CodeTwin ChaosLab

    The engine performs simulated chaos experiments
    without affecting real infrastructure
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
        Currently supports:
        -Services Down
        """

        #Ensure the experiment targets this system.
        if experiment.system_id != self.system.id:
            raise ValueError(
                f"Experiment targets system '{experiment.system_id}'."
                f"but engine contains system '{self.system.id}'"
            )

        #Ensure the target node exists.
        node_ids = {node.id for node in self.system.nodes}

        if experiment.target_node not in node_ids:
            raise ValueError(
                f"Target node '{experiment.target_node}'"
                f"does not exist in the system"
            )

        #For now, only service_down is supported.
        if experiment.type != "service_down":
            raise ValueError (
                f"Experiment type '{experiment.type}'"
                f"is not supported by the current ChaosEngine"
            )

        now = datetime.now(timezone.utc)

        #Finds nodes affected by the failed node.
        affected_nodes = self.graph.get_affected_nodes(
            experiment.target_node
        )

        #Events generated during the simulation.
        events =[]

        #Events: failure injected into the target node.
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

        # Events: affected nodes become degraded.
        for index, node_id in enumerate(affected_nodes):
            events.append(
                SimulationEvent(
                    id=f"event-{experiment.id}-{index}",
                    run_id=f"run-{experiment.id}",
                    node_id=node_id,
                    event_type="node_degraded",
                    severity=max(
                        0.1,
                        1.0 - ((index + 1)* 0.2)
                    ),
                    timestamp=now,
                )
            )

        #Simulated recovery information.
        recoveries= [
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

        #Create the simulation run after all results are know.
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