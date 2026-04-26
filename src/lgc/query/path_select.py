import networkx as nx

from lgc.domain.schemas import Edge, Node


def select_path_evidence(
    question: str,
    nodes: list[Node],
    edges: list[Edge],
    max_nodes: int = 32,
) -> tuple[list[Node], list[Edge]]:
    if not nodes:
        return [], []

    terms = _terms(question)
    node_by_id = {node.id: node for node in nodes}
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node.id)
    for edge in edges:
        if edge.source_id in node_by_id and edge.target_id in node_by_id:
            if _is_irrelevant_external(node_by_id[edge.source_id], terms) or _is_irrelevant_external(
                node_by_id[edge.target_id], terms
            ):
                continue
            graph.add_edge(edge.source_id, edge.target_id, id=edge.id, weight=_edge_weight(edge))

    seeds = _seed_nodes(nodes, terms)[: min(4, max_nodes)]
    selected_ids: set[str] = {node.id for node in seeds}

    # Multi-source BFS: expand neighbors from each seed to depth 1
    for seed in seeds:
        if len(selected_ids) >= max_nodes:
            break
        for neighbor_id in _bfs_expand(graph, seed.id, max_depth=1, limit=min(4, max_nodes - len(selected_ids))):
            neighbor = node_by_id.get(neighbor_id)
            if neighbor and neighbor.metadata.get("kind") != "external_symbol":
                selected_ids.add(neighbor_id)
            if len(selected_ids) >= max_nodes:
                break

    # Also include shortest-path nodes between seeds for connectivity
    for index, left in enumerate(seeds):
        for right in seeds[index + 1 :]:
            if len(selected_ids) >= max_nodes:
                break
            try:
                path = nx.shortest_path(graph, left.id, right.id, weight="weight")
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
            for node_id in path:
                selected_ids.add(node_id)
                if len(selected_ids) >= max_nodes:
                    break

    if not selected_ids:
        selected_ids = {nodes[0].id}

    selected_nodes = [node for node in nodes if node.id in selected_ids][:max_nodes]
    selected_edge_ids = _edge_ids_for_paths(graph, selected_ids)
    selected_edges = [edge for edge in edges if edge.id in selected_edge_ids]
    return selected_nodes, selected_edges


def _bfs_expand(graph: nx.Graph, start: str, max_depth: int = 2, limit: int = 16) -> list[str]:
    """BFS from start node, return neighbor nodes within max_depth."""
    visited: set[str] = {start}
    result: list[str] = []
    frontier = [start]
    for _depth in range(max_depth):
        next_frontier: list[str] = []
        for node_id in frontier:
            if not graph.has_node(node_id):
                continue
            for neighbor in sorted(graph.neighbors(node_id)):
                if neighbor not in visited:
                    visited.add(neighbor)
                    result.append(neighbor)
                    next_frontier.append(neighbor)
                    if len(result) >= limit:
                        return result
        frontier = next_frontier
    return result


def _seed_nodes(nodes: list[Node], terms: set[str]) -> list[Node]:
    scored = [(node, _term_score(node, terms)) for node in nodes]
    if any(score > 0 for _node, score in scored):
        scored = [(node, score) for node, score in scored if score > 0]
    return [
        node
        for node, _score in sorted(
            scored,
            key=lambda item: (item[1], float(item[0].metadata.get("importance_score", 0.0)), item[0].id),
            reverse=True,
        )
    ]


def _term_score(node: Node, terms: set[str]) -> int:
    if node.metadata.get("kind") == "external_symbol":
        haystack = " ".join([node.id, node.label, str(node.metadata.get("name", ""))]).lower()
    else:
        haystack = " ".join([node.id, node.label, str(node.metadata)]).lower()
    score = 0
    for term in terms:
        if term in haystack:
            score += 1
        elif len(term) >= 5 and term[:5] in haystack:
            score += 1
    return score


def _edge_weight(edge: Edge) -> float:
    kind = edge.kind.upper()
    if kind == "CALLS":
        return 0.5
    if kind == "CONTAINS":
        return 0.75
    if kind == "IMPORTS":
        return 1.0
    return 2.0


def _edge_ids_for_paths(graph: nx.Graph, selected_ids: set[str]) -> set[str]:
    edge_ids: set[str] = set()
    for left, right, data in graph.edges(data=True):
        if left in selected_ids and right in selected_ids and data.get("id"):
            edge_ids.add(data["id"])
    return edge_ids


def _is_irrelevant_external(node: Node, terms: set[str]) -> bool:
    return node.metadata.get("kind") == "external_symbol" and _term_score(node, terms) == 0


def _terms(question: str) -> set[str]:
    terms: set[str] = set()
    for part in question.replace("_", " ").replace("-", " ").split():
        cleaned = part.lower().strip(".,:;!?()[]{}\"'")
        if len(cleaned) <= 2 or cleaned in {"where", "what", "give", "implemented", "the", "does", "how", "are"}:
            continue
        terms.add(cleaned)
        # Suffix stripping for common English inflections
        for suffix in ("tion", "sion", "ment", "ness", "ing", "ed", "er", "es", "s", "al", "ly"):
            if cleaned.endswith(suffix) and len(cleaned) > len(suffix) + 3:
                terms.add(cleaned[: -len(suffix)])
                break
    return terms
