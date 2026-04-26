from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Edge, EvidenceSpan, Node
from lgc.graph.importance import annotate_importance
from lgc.query.path_select import select_path_evidence
from lgc.query.prune import strict_prune


def test_importance_adds_score_to_metadata() -> None:
    nodes = [_node("a"), _node("b")]
    edges = [_edge("e", "a", "b", "CALLS")]

    annotated = annotate_importance(nodes, edges)

    assert "importance_score" in annotated[1].metadata
    assert annotated[1].metadata["importance_score"] > 0


def test_path_select_keeps_shortest_path_between_relevant_nodes() -> None:
    nodes = [_node("auth"), _node("service"), _node("login_user")]
    edges = [_edge("e1", "auth", "service", "CONTAINS"), _edge("e2", "service", "login_user", "CALLS")]

    selected_nodes, selected_edges = select_path_evidence("auth login_user", nodes, edges, max_nodes=3)

    assert {node.id for node in selected_nodes} == {"auth", "service", "login_user"}
    assert {edge.id for edge in selected_edges} == {"e1", "e2"}


def test_strict_prune_respects_token_budget() -> None:
    nodes = [_node(f"node-{index}") for index in range(10)]

    selected_nodes, selected_edges, used_tokens = strict_prune("query", nodes, [], max_tokens=100)

    assert selected_edges == []
    assert used_tokens <= 100
    assert len(selected_nodes) < len(nodes)


def _node(node_id: str) -> Node:
    return Node(
        id=node_id,
        label=node_id,
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[EvidenceSpan(path=f"{node_id}.py", start_line=1, end_line=1)],
        metadata={"kind": "function", "path": f"{node_id}.py"},
    )


def _edge(edge_id: str, source_id: str, target_id: str, kind: str) -> Edge:
    return Edge(
        id=edge_id,
        source_id=source_id,
        target_id=target_id,
        kind=kind,
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[EvidenceSpan(path="a.py", start_line=1, end_line=1)],
    )
