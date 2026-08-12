from collections import defaultdict

def validate_no_cycles(
        nodes: list[str],
        dependencies: list[tuple[str, str]]
) -> None:
    """
    Validates that he dependency graph does not contain cycles.

    Each dependency is represented as:
        (source, target)

    Example:
        A -> B
        B -> C

    is valid.

    But:
        A -> B
        B -> C
        C -> A
    
    contains a cycle and is invalid.
    """

    graph = defaultdict(list)

    #Create the graph
    for node in nodes:
        graph[node]

    for source, target in dependencies:
        graph[source].append(target)

    #0 = not visited
    #1 = currently being visited
    #2 = completely visited
    state = {node: 0 for node in nodes}

    def visit(node: str) -> bool:
        #Node is currently in the recursion path.
        if state[node] == 1:
            return True

        #Node was already fully processed.
        if state[node] == 2:
            return False

        state[node] = 1

        for neighbor in graph[node]:
            if visit(neighbor):
                return True

        state[node] = 2
        return False

    for node in nodes:
        if state[node] == 0 and visit(node):
            raise ValueError("Dependency graph contains a cycle")
