from app.chaos.chaos_engine import ChaosEngine
from app.models.experiment import Experiment
from app.models.simulation_event import SimulationEvent
from app.models.simulation_run import SimulationRun
from app.models.system import System


class ChaosService:
    """
    Orchestrates the execution of chaos experiments.
    """

    def run_experiment(
        self,
        system: System,
        experiment: Experiment
    ) -> tuple[SimulationRun, list[SimulationEvent]]:
        """
        Executes an experiment using the ChaosEngine.
        """

        engine = ChaosEngine(system)

        return engine.run(experiment)