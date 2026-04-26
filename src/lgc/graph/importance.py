from collections import defaultdict

import networkx as nx

from lgc.domain.schemas import Edge, Node


def annotate_importance(nodes: list[Node], edges: list[Edge]) -> list[Node]:
    graph = nx.DiGraph()
    for node in nodes:
        graph.add_node(node.id)
    for edge in edges:
        graph.add_edge(edge.source_id, edge.target_id, kind=edge.kind)

    centrality = nx.degree_centrality(graph) if graph.number_of_nodes() else {}
    call_frequency: dict[str, int] = {}
    for edge in edges:
        if edge.kind.upper() == "CALLS":
            call_frequency[edge.target_id] = call_frequency.get(edge.target_id, 0) + 1

    cross_file = _cross_file_scores(nodes, edges)
    cross_module = _cross_module_scores(nodes, edges)

    annotated: list[Node] = []
    for node in nodes:
        score = (
            centrality.get(node.id, 0.0)
            + graph.in_degree(node.id) * 0.25
            + graph.out_degree(node.id) * 0.1
            + call_frequency.get(node.id, 0) * 0.5
            + cross_file.get(node.id, 0) * 0.75
            + cross_module.get(node.id, 0) * 1.0
        )
        metadata = {**node.metadata, "importance_score": round(score, 6)}
        annotated.append(node.model_copy(update={"metadata": metadata}))
    return annotated


def _cross_file_scores(nodes: list[Node], edges: list[Edge]) -> dict[str, float]:
    """Nodes referenced from multiple files get a higher score."""
    node_file: dict[str, str] = {}
    for node in nodes:
        path = node.metadata.get("path")
        if isinstance(path, str):
            node_file[node.id] = path

    referencing_files: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        source_file = node_file.get(edge.source_id)
        target_file = node_file.get(edge.target_id)
        if source_file and target_file and source_file != target_file:
            referencing_files[edge.target_id].add(source_file)
            referencing_files[edge.source_id].add(target_file)

    return {node_id: len(files) for node_id, files in referencing_files.items()}


def _cross_module_scores(nodes: list[Node], edges: list[Edge]) -> dict[str, float]:
    """Nodes connecting different top-level modules get a bonus."""
    node_module: dict[str, str] = {}
    for node in nodes:
        path = node.metadata.get("path", "")
        if isinstance(path, str):
            parts = path.replace("\\", "/").split("/")
            node_module[node.id] = parts[0] if parts else ""

    connecting_modules: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        src_mod = node_module.get(edge.source_id, "")
        tgt_mod = node_module.get(edge.target_id, "")
        if src_mod and tgt_mod and src_mod != tgt_mod:
            connecting_modules[edge.source_id].add(tgt_mod)
            connecting_modules[edge.target_id].add(src_mod)

    return {node_id: len(modules) for node_id, modules in connecting_modules.items()}
