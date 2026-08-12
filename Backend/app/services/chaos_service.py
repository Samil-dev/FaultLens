from app.chaos.chaos_engine import ChaosEngine
from app.models.experiment import Experiment
from app.models.simulation_event import SimulationEvent
from app.models.simulation_run import SimulationRun
from app.models.system import System
from app.services.metrics_service import MetricsService
from app.models.metric_comparison import MetricComparison
class ChaosService:
    """
    Orchestrates the execution of chaos experiments.
    """

    def run_experiment(
            self,
            system: System,
            experiment: Experiment
    ) -> tuple[
        SimulationRun,
        list[SimulationEvent],
        list[MetricComparison]
    ]:
        """
        Executes a chaos experiment and measures its simulated impact.
        """

        #Create the metrics service.
        metrics_service = MetricsService()

        #Capture the systeam state before the experiment.
        before_snapshot = metrics_service.create_snapshot(system)

        #Execute the chaos experiment.
        engine = ChaosEngine(system)

        run, events = engine.run(experiment)

        #Build the simulated state after the experiment.
        status_overrides = {
            experiment.target_node: "failed"
        }

        for node_id in run.affected_nodes:
            status_overrides[node_id] = "degraded"

        #Capture the system state after the experiment.
        after_snapshot = metrics_service.create_snapshot(
            system,
            status_overrides
        )

        #Compare Before vs After.
        comparisons = metrics_service.compare_snapshots(
            before_snapshot,
            after_snapshot
        )
        return run, events, comparisons