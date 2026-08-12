from typing import Literal

from app.models.metrics import Metrics
from app.models.system import System
from app.models.metric_snapshot import MetricSnapshot
from app.models.metric_comparison import MetricComparison

class MetricsService:
    """
    Service responsible for generating and working with
    simulated system metrics.
    """

    def get_node_metrics(
        self,
        system: System,
        node_id: str,
        simulated_status: Literal["healthy", "degraded", "failed"] = "healthy"
    ) -> Metrics:
        """
        Returns simulated metrics for a specific node.

        The metrics depend on the simulated state of the node.
        """

        # Verify that the requested node exists.
        node_ids = {node.id for node in system.nodes}

        if node_id not in node_ids:
            raise ValueError(
                f"Node '{node_id}' does not exist in the system"
            )

        if simulated_status == "healthy":
            return Metrics(
                node_id=node_id,
                cpu_usage=35.0,
                memory_usage=55.0,
                latency_ms=40.0,
                error_rate=0.2,
            )

        if simulated_status == "degraded":
            return Metrics(
                node_id=node_id,
                cpu_usage=70.0,
                memory_usage=68.0,
                latency_ms=220.0,
                error_rate=4.0,
            )

        if simulated_status == "failed":
            return Metrics(
                node_id=node_id,
                cpu_usage=95.0,
                memory_usage=90.0,
                latency_ms=1000.0,
                error_rate=25.0,
            )

        raise ValueError(
            f"Unsupported simulated status '{simulated_status}'"
        )
    
    def create_snapshot(
        self,
        system: System,
        status_overrides: dict[
            str,
            Literal["healthy", "degraded", "failed"]
        ] | None = None
    ) -> list[MetricSnapshot]:
        """
        Creates a metrics snapshot for every node in the system.

        status_overrides can be used to simulate node states.
        """

        snapshots = []

        if status_overrides is None:
            status_overrides = {}

        for node in system.nodes:

            simulated_status = status_overrides.get(
                node.id,
                "healthy"
            )

            metrics = self.get_node_metrics(
                system,
                node.id,
                simulated_status
            )

            snapshots.append(
                MetricSnapshot(
                    node_id=node.id,
                    metrics={
                        "cpu_usage": metrics.cpu_usage,
                        "memory_usage": metrics.memory_usage,
                        "latency_ms": metrics.latency_ms,
                        "error_rate": metrics.error_rate,
                    }
                )
            )

        return snapshots

    def compare_snapshots(
        self,
        before: list[MetricSnapshot],
        after: list[MetricSnapshot]
    ) -> list[MetricComparison]:
        """
        Compares two sets of metric snapshots.
        """

        before_by_node = {
            snapshot.node_id: snapshot
            for snapshot in before
        }

        after_by_node = {
            snapshot.node_id: snapshot
            for snapshot in after
        }

        comparisons = []

        for node_id, before_snapshot in before_by_node.items():

            after_snapshot = after_by_node.get(node_id)

            if after_snapshot is None:
                continue

            comparisons.append(
                MetricComparison(
                    node_id=node_id,
                    cpu_usage_delta=(
                        after_snapshot.metrics["cpu_usage"]
                        - before_snapshot.metrics["cpu_usage"]
                    ),
                    memory_usage_delta=(
                        after_snapshot.metrics["memory_usage"]
                        - before_snapshot.metrics["memory_usage"]
                    ),
                    latency_delta_ms=(
                        after_snapshot.metrics["latency_ms"]
                        - before_snapshot.metrics["latency_ms"]
                    ),
                    error_rate_delta=(
                        after_snapshot.metrics["error_rate"]
                        - before_snapshot.metrics["error_rate"]
                    ),
                )
            )

        return comparisons