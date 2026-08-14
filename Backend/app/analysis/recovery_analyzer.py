from app.models.recovery_analysis import RecoveryAnalysis
from app.models.simulation_run import SimulationRun


class RecoveryAnalyzer:
    """
    Analyzes node recovery after a chaos experiment.
    """

    def analyze(
        self,
        run: SimulationRun
    ) -> RecoveryAnalysis:
        """
        Calculates recovery statistics.
        """

        recoveries = run.recoveries

        if not recoveries:
            return RecoveryAnalysis(
                recovered_nodes=0,
                total_recovery_nodes=0,
                average_recovery_seconds=0.0,
                max_recovery_seconds=0.0,
                failed_recoveries=[],
            )

        recovered = [
            recovery
            for recovery in recoveries
            if recovery.recovery_status == "recovered"
            and recovery.recovery_time_seconds is not None
        ]

        failed = [
            recovery.node_id
            for recovery in recoveries
            if recovery.recovery_status == "failed"
        ]

        recovery_times = [
            recovery.recovery_time_seconds
            for recovery in recovered
            if recovery.recovery_time_seconds is not None
        ]

        average_recovery = (
            sum(recovery_times) / len(recovery_times)
            if recovery_times
            else 0.0
        )

        max_recovery = max(
            recovery_times,
            default=0.0
        )

        return RecoveryAnalysis(
            recovered_nodes=len(recovered),
            total_recovery_nodes=len(recoveries),
            average_recovery_seconds=round(
                average_recovery,
                2
            ),
            max_recovery_seconds=round(
                max_recovery,
                2
            ),
            failed_recoveries=failed,
        )