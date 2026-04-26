from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import EvidenceSpan, Node
from lgc.query.classify import QueryIntent, classify_query
from lgc.query.route import route_query


def node(node_id: str, label: str, layer: Layer, path: str = "src/api.py") -> Node:
    support = []
    truth = TruthLabel.INFERRED
    if layer == Layer.L0:
        truth = TruthLabel.EXTRACTED
        support = [EvidenceSpan(path=path, start_line=1, end_line=1)]
    support_node_ids = ["support:a"] if layer != Layer.L0 else []
    return Node(
        id=node_id,
        label=label,
        layer=layer,
        truth=truth,
        confidence=1.0,
        support=support,
        support_node_ids=support_node_ids,
        metadata={"path": path, "summary": label},
    )


def test_classify_query_uses_expected_intents() -> None:
    assert classify_query("give me project overview") == QueryIntent.OVERVIEW
    assert classify_query("where is Service implemented") == QueryIntent.IMPLEMENTATION_LOCALIZATION
    assert classify_query("trace call flow") == QueryIntent.FLOW_TRACING


def test_route_query_prefers_overview_layers() -> None:
    nodes = [
        node("l0:service", "Service", Layer.L0),
        node("l2:api", "api", Layer.L2),
        node("l3:api", "api overview", Layer.L3),
    ]

    packet = route_query("architecture overview", nodes, [], max_tokens=2048)

    assert packet.metadata["intent"] == "overview"
    assert packet.metadata["route_layers"] == ["L3", "L2", "L1"]
    assert packet.nodes[0].layer == Layer.L3


def test_route_query_prefers_implementation_layers() -> None:
    nodes = [
        node("l3:api", "api overview", Layer.L3),
        node("l1:api", "api file", Layer.L1),
        node("l0:service", "Service", Layer.L0),
    ]

    packet = route_query("where is Service implemented", nodes, [], max_tokens=2048)

    assert packet.metadata["intent"] == "implementation-localization"
    assert packet.nodes[0].layer == Layer.L0
    assert packet.nodes[0].label == "Service"
