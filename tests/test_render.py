from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import EvidencePacket, EvidenceSpan, Node
from lgc.query.render import MarkdownRenderer


def test_markdown_renderer_contains_required_sections() -> None:
    packet = EvidencePacket(query="where", nodes=[_node()])

    rendered = MarkdownRenderer().render(packet)

    assert "# Answer" in rendered
    assert "## Direct Answer" in rendered
    assert "## Supporting Evidence" in rendered
    assert "## Relevant Files" in rendered
    assert "## Confidence Notes" in rendered


def test_markdown_renderer_empty_packet_is_safe() -> None:
    rendered = MarkdownRenderer().render(EvidencePacket(query="unknown"))

    assert "No supported evidence was found in the current graph." in rendered


def test_markdown_renderer_includes_file_paths_from_spans() -> None:
    rendered = MarkdownRenderer().render(EvidencePacket(query="where", nodes=[_node()]))

    assert "`src/example.py`" in rendered
    assert "lines 2-4" in rendered


def _node() -> Node:
    return Node(
        id="node:example",
        label="example",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=0.9,
        support=[EvidenceSpan(path="src/example.py", start_line=2, end_line=4)],
        metadata={"kind": "function"},
    )
