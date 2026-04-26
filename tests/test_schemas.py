import pytest
from pydantic import ValidationError

from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Edge, EvidencePacket, EvidenceSpan, Node


def span() -> EvidenceSpan:
    return EvidenceSpan(path="src/example.py", start_line=1, end_line=3)


def test_evidence_span_rejects_reversed_lines() -> None:
    with pytest.raises(ValidationError, match="end_line"):
        EvidenceSpan(path="src/example.py", start_line=4, end_line=3)


def test_node_accepts_extracted_fact_with_support() -> None:
    node = Node(
        id="node:module:example",
        label="example",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[span()],
        metadata={"kind": "module"},
    )

    assert node.support[0].path == "src/example.py"
    assert node.metadata["kind"] == "module"


def test_edge_accepts_extracted_fact_with_support() -> None:
    edge = Edge(
        id="edge:imports",
        source_id="node:module:a",
        target_id="node:module:b",
        kind="IMPORTS",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=0.9,
        support=[span()],
    )

    assert edge.kind == "IMPORTS"


def test_extracted_node_requires_support() -> None:
    with pytest.raises(ValidationError, match="EXTRACTED facts"):
        Node(
            id="node:unsupported",
            label="unsupported",
            layer=Layer.L0,
            truth=TruthLabel.EXTRACTED,
            confidence=0.8,
        )


def test_extracted_edge_requires_support() -> None:
    with pytest.raises(ValidationError, match="EXTRACTED facts"):
        Edge(
            id="edge:unsupported",
            source_id="node:a",
            target_id="node:b",
            kind="CALLS",
            layer=Layer.L0,
            truth=TruthLabel.EXTRACTED,
            confidence=0.8,
        )


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_confidence_must_be_between_zero_and_one(confidence: float) -> None:
    with pytest.raises(ValidationError):
        Node(
            id="node:bad-confidence",
            label="bad-confidence",
            layer=Layer.L0,
            truth=TruthLabel.INFERRED,
            confidence=confidence,
        )


def test_evidence_packet_groups_nodes_and_edges() -> None:
    node = Node(
        id="node:summary:file",
        label="file_summary",
        layer=Layer.L1,
        truth=TruthLabel.INFERRED,
        confidence=1.0,
        support_node_ids=["node:module:example"],
    )

    packet = EvidencePacket(query="overview", nodes=[node], token_budget=512)

    assert packet.nodes == [node]
    assert packet.edges == []
