from lgc.agents.answer_auditor import AnswerAuditor
from lgc.agents.base import ValidationContext
from lgc.agents.compression_validator import CompressionValidator
from lgc.agents.parser_agent import ParserAgent
from lgc.agents.provenance_validator import ProvenanceValidator
from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Edge, EvidenceSpan, Node


def test_provenance_validator_rejects_missing_support() -> None:
    invalid = Node.model_construct(
        id="n2",
        label="bad",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[],
        support_node_ids=[],
        metadata={"kind": "function"},
    )

    report = ProvenanceValidator().validate(ValidationContext(nodes_l0=[_valid_l0_node(), invalid]))

    assert not report.passed
    assert report.errors


def test_compression_validator_rejects_missing_support_node_ids() -> None:
    invalid = Node(id="l1", label="file", layer=Layer.L1, truth=TruthLabel.INFERRED, confidence=1.0)

    report = CompressionValidator().validate(ValidationContext(nodes_l1=[invalid]))

    assert not report.passed


def test_answer_auditor_rejects_ungrounded_sentence() -> None:
    report = AnswerAuditor().validate("Function n1 handles login. This is important.", ["n1"])

    assert not report.passed


def test_parser_agent_rejects_missing_edge_endpoint() -> None:
    edge = Edge(
        id="e1",
        source_id="n1",
        target_id="missing",
        kind="CALLS",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[EvidenceSpan(path="a.py", start_line=1, end_line=1)],
    )

    report = ParserAgent().validate(ValidationContext(nodes_l0=[_valid_l0_node()], edges_l0=[edge]))

    assert not report.passed
    assert "missing target" in report.errors[0]


def _valid_l0_node() -> Node:
    return Node(
        id="n1",
        label="func",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[EvidenceSpan(path="a.py", start_line=1, end_line=3)],
        metadata={"kind": "function"},
    )
