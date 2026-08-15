from collections import defaultdict, deque

from app.models.system import System


class DependencyGraph:
    """
    Represents the dependency relationships of a CodeTwin system.
    """

    def __init__(self, system: System):
        self.system = system
        self.graph = self._build_graph()

    def _build_graph(self) -> dict[str, list[str]]:
        """
        Builds an adjacency map.

        Example:

        frontend -> api
        api -> database

        becomes:

        {
            "frontend": ["api"],
            "api": ["database"],
            "database": []
        }
        """

        graph = defaultdict(list)

        # Add every node to the graph.
        for node in self.system.nodes:
            graph[node.id]

        # Add the explicit dependencies.
        for dependency in self.system.dependencies:
            graph[dependency.source].append(dependency.target)

        return dict(graph)

    def get_affected_nodes(self, failed_node_id: str) -> list[str]:
        """
        Returns the nodes affected by a failed node, each appearing exactly once.

        Uses the reverse dependency graph to find which nodes depend on the
        failed node, traversing transitively via BFS.

        Deduplication is enforced at enqueue time: a node is added to the queue
        and to the affected list at most once, regardless of how many upstream
        paths lead to it.
        """

        reverse_graph = defaultdict(list)

        # Build the reverse graph.
        for source, targets in self.graph.items():
            for target in targets:
                reverse_graph[target].append(source)

        # Unknown node.
        if failed_node_id not in self.graph:
            return []

        affected = []
        enqueued = {failed_node_id}   # tracks every node that has entered the queue
        queue = deque([failed_node_id])

        while queue:
            current = queue.popleft()

            for dependent in reverse_graph.get(current, []):
                if dependent not in enqueued:
                    enqueued.add(dependent)
                    affected.append(dependent)
                    queue.append(dependent)

        return affected