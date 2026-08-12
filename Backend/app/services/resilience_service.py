from app.models.metric_comparison import MetricComparison
from app.models.resilience_score import ResilienceScore


class ResilienceService:
    """
    Calculates a deterministic resilience score for the MVP.
    """

    # Reference maximums used to normalize metric changes.
    CPU_MAX_DELTA = 100.0
    MEMORY_MAX_DELTA = 100.0
    LATENCY_MAX_DELTA = 1000.0
    ERROR_RATE_MAX_DELTA = 25.0

    def calculate_score(
        self,
        comparisons: list[MetricComparison],
        affected_nodes: int,
        total_nodes: int
    ) -> ResilienceScore:
        """
        Calculates a resilience score from 0 to 100.

        The score combines:
        - Blast radius
        - Metric impact
        """

        if total_nodes <= 0:
            raise ValueError("Total nodes must be greater than zero")

        if affected_nodes < 0:
            raise ValueError("Affected nodes cannot be negative")

        if affected_nodes > total_nodes:
            raise ValueError(
                "Affected nodes cannot exceed total nodes"
            )

        # Calculate the percentage of the system affected.
        blast_radius = affected_nodes / total_nodes

        # Calculate average metric impact.
        metric_impact = self._calculate_metric_impact(comparisons)

        # Combine both factors equally.
        score = 100.0 * (
            1.0
            - (0.5 * blast_radius)
            - (0.5 * metric_impact)
        )

        # Keep the score inside the valid range.
        score = max(0.0, min(100.0, score))

        return ResilienceScore(
            score=round(score, 2),
            rating=self._get_rating(score),
            affected_nodes=affected_nodes,
            total_nodes=total_nodes,
        )

    def _calculate_metric_impact(
        self,
        comparisons: list[MetricComparison]
    ) -> float:
        """
        Calculates the average normalized metric impact.
        """

        if not comparisons:
            return 0.0

        total_impact = 0.0

        for comparison in comparisons:

            cpu_impact = min(
                abs(comparison.cpu_usage_delta)
                / self.CPU_MAX_DELTA,
                1.0
            )

            memory_impact = min(
                abs(comparison.memory_usage_delta)
                / self.MEMORY_MAX_DELTA,
                1.0
            )

            latency_impact = min(
                abs(comparison.latency_delta_ms)
                / self.LATENCY_MAX_DELTA,
                1.0
            )

            error_impact = min(
                abs(comparison.error_rate_delta)
                / self.ERROR_RATE_MAX_DELTA,
                1.0
            )

            node_impact = (
                cpu_impact
                + memory_impact
                + latency_impact
                + error_impact
            ) / 4.0

            total_impact += node_impact

        return total_impact / len(comparisons)

    def _get_rating(self, score: float) -> str:
        """
        Converts the numerical score into a readable rating.
        """

        if score >= 80:
            return "excellent"

        if score >= 60:
            return "good"

        if score >= 40:
            return "moderate"

        if score >= 20:
            return "poor"

        return "critical"