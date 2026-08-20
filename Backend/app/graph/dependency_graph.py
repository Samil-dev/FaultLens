from collections import defaultdict, deque

from app.models.system import System


class DependencyGraph:
    """
    Represents the dependency relationships of a FaultLens system.
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

    def _reverse_graph(self) -> dict[str, list[str]]:
        reverse_graph = defaultdict(list)
        for source, targets in self.graph.items():
            for target in targets:
                reverse_graph[target].append(source)
        return reverse_graph

    def get_affected_nodes(
        self,
        failed_node_id: str,
        max_depth: int | None = None,
    ) -> list[str]:
        """
        Returns the nodes affected by a failed node, each appearing exactly once.

        Uses the reverse dependency graph to find which nodes depend on the
        failed node, traversing transitively via BFS.

        Deduplication is enforced at enqueue time: a node is added to the queue
        and to the affected list at most once, regardless of how many upstream
        paths lead to it.

        `max_depth`, when given, caps how many hops the failure is allowed to
        cascade (1 = only direct dependents, 2 = dependents of dependents,
        ...). Defaults to unlimited (today's behavior) — this exists so
        callers can make propagation depth a function of something real,
        e.g. how long an experiment ran, without changing the default
        traversal every existing caller relies on.
        """

        reverse_graph = self._reverse_graph()

        # Unknown node.
        if failed_node_id not in self.graph:
            return []

        affected = []
        enqueued = {failed_node_id}   # tracks every node that has entered the queue
        queue = deque([(failed_node_id, 0)])

        while queue:
            current, depth = queue.popleft()

            if max_depth is not None and depth >= max_depth:
                continue

            for dependent in reverse_graph.get(current, []):
                if dependent not in enqueued:
                    enqueued.add(dependent)
                    affected.append(dependent)
                    queue.append((dependent, depth + 1))

        return affected

    def get_affected_node_depths(self, failed_node_id: str) -> dict[str, int]:
        """
        Same traversal as get_affected_nodes(), but returns each affected
        node's hop distance from the failed node (1 = direct dependent, 2 =
        a dependent of a dependent, ...) instead of a flat list — lets a
        caller reason about *how far* a node is from the origin, e.g. to
        decide whether a long-running experiment leaves it unable to fully
        recover.
        """

        reverse_graph = self._reverse_graph()

        if failed_node_id not in self.graph:
            return {}

        depths: dict[str, int] = {}
        enqueued = {failed_node_id}
        queue = deque([(failed_node_id, 0)])

        while queue:
            current, depth = queue.popleft()
            for dependent in reverse_graph.get(current, []):
                if dependent not in enqueued:
                    enqueued.add(dependent)
                    depths[dependent] = depth + 1
                    queue.append((dependent, depth + 1))

        return depths