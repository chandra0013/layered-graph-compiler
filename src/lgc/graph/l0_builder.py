import json
from pathlib import Path

import networkx as nx

from lgc.domain.enums import TruthLabel
from lgc.domain.schemas import Edge, Node


class L0GraphError(ValueError):
    """Raised when L0 graph inputs violate compiler invariants."""


def build_l0_graph(nodes: list[Node], edges: list[Edge]) -> nx.MultiDiGraph:
    _validate_l0_inputs(nodes, edges)

    graph = nx.MultiDiGraph(layer="L0")
    for node in nodes:
        graph.add_node(node.id, **node.model_dump(mode="json"))

    for edge in edges:
        graph.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge.id,
            **edge.model_dump(mode="json"),
        )

    return graph


def export_l0_json(
    nodes: list[Node],
    edges: list[Edge],
    output_path: Path,
) -> None:
    _validate_l0_inputs(nodes, edges)
    payload = {
        "layer": "L0",
        "nodes": [node.model_dump(mode="json") for node in nodes],
        "edges": [edge.model_dump(mode="json") for edge in edges],
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _validate_l0_inputs(nodes: list[Node], edges: list[Edge]) -> None:
    node_ids = [node.id for node in nodes]
    edge_ids = [edge.id for edge in edges]

    if len(node_ids) != len(set(node_ids)):
        raise L0GraphError("node_id must be unique")
    if len(edge_ids) != len(set(edge_ids)):
        raise L0GraphError("edge_id must be unique")

    node_id_set = set(node_ids)
    for edge in edges:
        if edge.source_id not in node_id_set:
            raise L0GraphError(f"edge source_id is missing: {edge.source_id}")
        if edge.target_id not in node_id_set:
            raise L0GraphError(f"edge target_id is missing: {edge.target_id}")

    for fact in [*nodes, *edges]:
        if fact.truth == TruthLabel.EXTRACTED and not fact.support:
            raise L0GraphError("EXTRACTED objects must include support")
