from app.models.experiment import Experiment
from app.models.impact_analysis import ImpactAnalysis
from app.models.metric_comparison import MetricComparison
from app.models.simulation_run import SimulationRun


class ImpactAnalyzer:
    """
    Analyzes the structural and metric impact of a chaos experiment.
    """

    CPU_MAX_DELTA = 100.0
    MEMORY_MAX_DELTA = 100.0
    LATENCY_MAX_DELTA = 1000.0
    ERROR_RATE_MAX_DELTA = 25.0

    def analyze(
        self,
        experiment: Experiment,
        run: SimulationRun,
        comparisons: list[MetricComparison],
        total_nodes: int
    ) -> ImpactAnalysis:
        """
        Calculates blast radius and identifies critical nodes.
        """

        if total_nodes <= 0:
            raise ValueError("Total nodes must be greater than zero")

        affected_count = len(run.affected_nodes)

        blast_radius = affected_count / total_nodes

        node_impacts: dict[str, float] = {}

        for comparison in comparisons:
            node_impacts[comparison.node_id] = self._calculate_node_impact(
                comparison
            )

        average_metric_impact = (
            sum(node_impacts.values()) / len(node_impacts)
            if node_impacts
            else 0.0
        )

        critical_nodes = [
            comparison.node_id
            for comparison in comparisons
            if self._calculate_node_impact(comparison) >= 0.5
        ]

        # The target of a service_down experiment is always important.
        if (
            experiment.target_node
            not in critical_nodes
            and experiment.target_node in {
                comparison.node_id for comparison in comparisons
            }
        ):
            critical_nodes.insert(0, experiment.target_node)

        return ImpactAnalysis(
            blast_radius=round(blast_radius, 4),
            affected_nodes=affected_count,
            total_nodes=total_nodes,
            critical_nodes=critical_nodes,
            average_metric_impact=round(
                average_metric_impact,
                4
            ),
        )

    def _calculate_node_impact(
        self,
        comparison: MetricComparison
    ) -> float:
        """
        Normalizes the metric changes for a single node.
        """

        cpu_impact = min(
            abs(comparison.cpu_usage_delta) / self.CPU_MAX_DELTA,
            1.0
        )

        memory_impact = min(
            abs(comparison.memory_usage_delta) / self.MEMORY_MAX_DELTA,
            1.0
        )

        latency_impact = min(
            abs(comparison.latency_delta_ms) / self.LATENCY_MAX_DELTA,
            1.0
        )

        error_impact = min(
            abs(comparison.error_rate_delta) / self.ERROR_RATE_MAX_DELTA,
            1.0
        )

        return (
            cpu_impact
            + memory_impact
            + latency_impact
            + error_impact
        ) / 4.0