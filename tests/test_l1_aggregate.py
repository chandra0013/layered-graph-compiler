from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import EvidenceSpan, Node
from lgc.graph.l1_aggregate import aggregate_l1_file_summaries


def l0_node(node_id: str, kind: str, path: str = "src/example.py") -> Node:
    return Node(
        id=node_id,
        label=node_id,
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[EvidenceSpan(path=path, start_line=1, end_line=1)],
        metadata={"kind": kind, "path": path},
    )


def test_aggregate_l1_file_summaries_counts_symbols_by_file() -> None:
    summaries = aggregate_l1_file_summaries(
        [
            l0_node("node:module", "module"),
            l0_node("node:import", "import"),
            l0_node("node:class", "class"),
            l0_node("node:function", "function"),
            l0_node("node:method", "method"),
        ]
    )

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.id == "l1:file_summary:src/example.py"
    assert summary.label == "file_summary"
    assert summary.layer == Layer.L1
    assert summary.truth == TruthLabel.INFERRED
    assert summary.support_node_ids == [
        "node:class",
        "node:function",
        "node:import",
        "node:method",
        "node:module",
    ]
    assert summary.metadata["symbol_count"] == 5
    assert summary.metadata["class_count"] == 1
    assert summary.metadata["function_count"] == 1
    assert summary.metadata["method_count"] == 1
    assert summary.metadata["import_count"] == 1


def test_aggregate_l1_file_summaries_creates_one_summary_per_file() -> None:
    summaries = aggregate_l1_file_summaries(
        [
            l0_node("node:a", "module", "src/a.py"),
            l0_node("node:b", "module", "src/b.py"),
        ]
    )

    assert [summary.metadata["path"] for summary in summaries] == ["src/a.py", "src/b.py"]


def test_aggregate_l1_file_summaries_can_use_support_path() -> None:
    node = Node(
        id="node:no-metadata-path",
        label="helper",
        layer=Layer.L0,
        truth=TruthLabel.EXTRACTED,
        confidence=1.0,
        support=[EvidenceSpan(path="src/support.py", start_line=1, end_line=1)],
        metadata={"kind": "function"},
    )

    summaries = aggregate_l1_file_summaries([node])

    assert summaries[0].metadata["path"] == "src/support.py"
    assert summaries[0].support_node_ids == ["node:no-metadata-path"]
