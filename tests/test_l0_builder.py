import json

import pytest

from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Edge, EvidenceSpan, Node
from lgc.graph.l0_builder import L0GraphError, build_l0_graph, export_l0_json


def span() -> EvidenceSpan:
    return EvidenceSpan(path="src/example.py", start_line=1, end_line=1)


def node(node_id: str) -> Node:
    return Node(
        id=node_id,
        label=node_id,
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[span()],
        metadata={"kind": "test"},
    )


def edge(edge_id: str, source_id: str = "node:a", target_id: str = "node:b") -> Edge:
    return Edge(
        id=edge_id,
        source_id=source_id,
        target_id=target_id,
        kind="CALLS",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[span()],
    )


def test_build_l0_graph_preserves_nodes_edges_and_metadata() -> None:
    nodes = [node("node:a"), node("node:b")]
    edges = [edge("edge:a-b")]

    graph = build_l0_graph(nodes, edges)

    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1
    assert graph.nodes["node:a"]["metadata"] == {"kind": "test"}
    assert graph["node:a"]["node:b"]["edge:a-b"]["kind"] == "CALLS"


def test_build_l0_graph_rejects_duplicate_node_ids() -> None:
    with pytest.raises(L0GraphError, match="node_id"):
        build_l0_graph([node("node:a"), node("node:a")], [])


def test_build_l0_graph_rejects_duplicate_edge_ids() -> None:
    nodes = [node("node:a"), node("node:b")]
    with pytest.raises(L0GraphError, match="edge_id"):
        build_l0_graph(nodes, [edge("edge:a-b"), edge("edge:a-b")])


def test_build_l0_graph_rejects_missing_edge_endpoint() -> None:
    with pytest.raises(L0GraphError, match="target_id"):
        build_l0_graph([node("node:a")], [edge("edge:a-b")])


def test_build_l0_graph_rejects_extracted_without_support() -> None:
    unsupported = Node.model_construct(
        id="node:bad",
        label="bad",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[],
        support_node_ids=[],
        metadata={},
    )

    with pytest.raises(L0GraphError, match="support"):
        build_l0_graph([unsupported], [])


def test_export_l0_json_writes_nodes_and_edges(tmp_path) -> None:
    output = tmp_path / "graph_l0.json"

    export_l0_json([node("node:a"), node("node:b")], [edge("edge:a-b")], output)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["layer"] == "L0"
    assert payload["nodes"][0]["id"] == "node:a"
    assert payload["edges"][0]["id"] == "edge:a-b"
