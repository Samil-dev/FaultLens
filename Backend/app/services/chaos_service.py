from app.chaos import duration_model
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

        # Create the metrics service.
        metrics_service = MetricsService()

        # Capture the system state before the experiment.
        before_snapshot = metrics_service.create_snapshot(system)

        # Execute the chaos experiment.
        engine = ChaosEngine(system)
        run, events = engine.run(experiment)

        # Determine target node status for metrics:
        # service_down → "failed"; all other supported types → "degraded".
        target_status = "failed" if experiment.type == "service_down" else "degraded"

        # Build the simulated state after the experiment.
        status_overrides = {
            experiment.target_node: target_status
        }

        for node_id in run.affected_nodes:
            status_overrides[node_id] = "degraded"

        # Capture the system state after the experiment. How far the
        # degraded/failed metrics move from their healthy baseline scales
        # with how long the experiment ran — see app.chaos.duration_model.
        after_snapshot = metrics_service.create_snapshot(
            system,
            status_overrides,
            experiment_type=experiment.type,
            severity_factor=duration_model.severity_factor(experiment.duration_seconds),
        )

        # Compare Before vs After.
        comparisons = metrics_service.compare_snapshots(
            before_snapshot,
            after_snapshot
        )
        return run, events, comparisons
