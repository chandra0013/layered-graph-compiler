import pytest

from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Edge, EvidenceSpan, Node
from lgc.validate.compression_guard import CompressionGuard
from lgc.validate.provenance_guard import ProvenanceGuard
from lgc.validate.schema_guard import SchemaGuard


def span() -> EvidenceSpan:
    return EvidenceSpan(path="example.py", start_line=1, end_line=1)


def test_schema_guard_validates_payload() -> None:
    payload = {
        "id": "node:a",
        "label": "a",
        "layer": "L0",
        "truth": "EXTRACTED",
        "confidence": 1.0,
        "support": [{"path": "example.py", "start_line": 1, "end_line": 1}],
    }

    node = SchemaGuard().validate(Node, payload)

    assert node.id == "node:a"


def test_provenance_guard_rejects_extracted_without_support() -> None:
    node = Node.model_construct(
        id="node:bad",
        label="bad",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[],
        support_node_ids=[],
        metadata={},
    )

    with pytest.raises(ValueError, match="provenance"):
        ProvenanceGuard().validate([node], [])


def test_provenance_guard_accepts_supported_extracted_edge() -> None:
    edge = Edge(
        id="edge:a-b",
        source_id="node:a",
        target_id="node:b",
        kind="CALLS",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[span()],
    )

    ProvenanceGuard().validate([], [edge])


def test_compression_guard_requires_support_node_ids() -> None:
    node = Node(
        id="l1:file:example.py",
        label="file_summary",
        layer=Layer.L1,
        truth=TruthLabel.INFERRED,
        confidence=1.0,
    )

    with pytest.raises(ValueError, match="support_node_ids"):
        CompressionGuard().validate([node])
