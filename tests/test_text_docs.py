from lgc.extract.text_docs import extract_text_document
from lgc.pipeline import build_project


def test_text_docs_extract_markdown_headings_paragraphs_rationale_and_links(tmp_path) -> None:
    doc = tmp_path / "architecture.md"
    doc.write_text(
        "# Architecture\n\nWHY: We use layered compression.\n\nSee [Graphify](https://example.com/graphify).\nPlain https://example.com/docs\n",
        encoding="utf-8",
    )

    nodes, edges = extract_text_document(doc, logical_path="docs/architecture.md")
    kinds = {node.metadata["kind"] for node in nodes}
    labels = {node.label for node in nodes}

    assert {"document", "heading", "rationale", "paragraph", "link"} <= kinds
    assert "Architecture" in labels
    assert any(edge.kind == "RATIONALE_FOR" for edge in edges)
    assert any(edge.kind == "REFERENCES" for edge in edges)
    assert all(node.support for node in nodes)
    assert all(edge.support for edge in edges)


def test_text_docs_provenance_line_numbers(tmp_path) -> None:
    doc = tmp_path / "notes.txt"
    doc.write_text("Intro\n\nNOTE: source span\n", encoding="utf-8")

    nodes, _edges = extract_text_document(doc, logical_path="notes.txt")
    rationale = next(node for node in nodes if node.metadata["kind"] == "rationale")

    assert rationale.support[0].path == "notes.txt"
    assert rationale.support[0].start_line == 3
    assert rationale.support[0].end_line == 3


def test_build_includes_document_nodes(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# Project\n\nA paragraph.\n", encoding="utf-8")

    counts = build_project(tmp_path)

    assert counts["l0_nodes"] >= 3
