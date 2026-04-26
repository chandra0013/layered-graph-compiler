from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import EvidenceSpan, Node
from lgc.query.classify import QueryIntent
from lgc.query.scoring import (
    adaptive_max_nodes,
    filter_noise,
    is_noise,
    score_candidate,
)


def _node(node_id: str, label: str, kind: str = "function", path: str = "src/api.py", **kwargs) -> Node:
    return Node(
        id=node_id,
        label=label,
        layer=kwargs.get("layer", Layer.L0),
        truth=TruthLabel.EXTRACTED,
        confidence=kwargs.get("confidence", 1.0),
        support=[EvidenceSpan(path=path, start_line=1, end_line=1)],
        metadata={"kind": kind, "path": path, "importance_score": kwargs.get("importance_score", 0.5)},
    )


def test_score_gives_higher_score_to_exact_query_match() -> None:
    matching = _node("py:function:auth.py:login_user", "login_user", path="auth.py")
    unrelated = _node("py:function:utils.py:helper", "helper", path="utils.py")
    terms = {"login", "user", "auth"}

    match_score = score_candidate(matching, terms, QueryIntent.IMPLEMENTATION_LOCALIZATION, [Layer.L1, Layer.L0])
    other_score = score_candidate(unrelated, terms, QueryIntent.IMPLEMENTATION_LOCALIZATION, [Layer.L1, Layer.L0])

    assert match_score > other_score


def test_external_symbol_filtered_unless_dependency_query() -> None:
    ext = _node("py:symbol:json.dumps", "json.dumps", kind="external_symbol")

    # Not a dependency query — should be noise
    assert is_noise(ext, {"route", "query"}, QueryIntent.ARCHITECTURE, term_score=0, graph_distance=0)

    # Dependency query — should NOT be noise
    assert not is_noise(ext, {"import", "dependency"}, QueryIntent.ARCHITECTURE, term_score=0, graph_distance=0)


def test_generic_labels_filtered_with_zero_overlap() -> None:
    generic = _node("py:function:app.py:main", "main", path="app.py")

    assert is_noise(generic, {"route", "query"}, QueryIntent.ARCHITECTURE, term_score=0, graph_distance=0)


def test_generic_labels_kept_if_query_matches() -> None:
    generic = _node("py:function:app.py:main", "main", path="app.py")

    # term_score > 0 means the query actually references this node
    assert not is_noise(generic, {"main"}, QueryIntent.IMPLEMENTATION_LOCALIZATION, term_score=1, graph_distance=0)


def test_low_confidence_inferred_filtered() -> None:
    low_conf = Node(
        id="low:node",
        label="maybe",
        layer=Layer.L1,
        truth=TruthLabel.INFERRED,
        confidence=0.3,
        support_node_ids=["a"],
        metadata={"kind": "file_summary"},
    )

    assert is_noise(low_conf, {"route"}, QueryIntent.ARCHITECTURE, term_score=0, graph_distance=0)


def test_filter_noise_returns_count() -> None:
    nodes = [
        _node("py:function:auth.py:login", "login", path="auth.py"),
        _node("py:symbol:json.dumps", "json.dumps", kind="external_symbol"),
        _node("py:function:app.py:main", "main", path="app.py"),
    ]

    kept, filtered = filter_noise(nodes, {"login", "auth"}, QueryIntent.IMPLEMENTATION_LOCALIZATION)

    assert filtered >= 1
    assert len(kept) < len(nodes)


def test_adaptive_max_nodes_varies_by_intent() -> None:
    impl = adaptive_max_nodes(QueryIntent.IMPLEMENTATION_LOCALIZATION)
    arch = adaptive_max_nodes(QueryIntent.ARCHITECTURE)

    assert impl < arch


def test_precision_smoke_on_small_project(tmp_path) -> None:
    """Ensure precision doesn't collapse on a trivial project."""
    import json

    from lgc.benchmark.run import run_benchmark

    (tmp_path / "auth.py").write_text("def login_user():\n    return True\n", encoding="utf-8")
    questions = tmp_path / "benchmark_questions.json"
    questions.write_text(
        json.dumps(
            [
                {
                    "question": "where is login_user defined",
                    "expected_nodes": ["login_user"],
                    "type": "implementation",
                    "difficulty": "easy",
                }
            ]
        ),
        encoding="utf-8",
    )

    report = run_benchmark(tmp_path, questions)

    assert report["precision"] > 0
    assert report["recall"] > 0
    assert "diagnostics" in report
    assert report["diagnostics"]["avg_returned_candidates"] > 0
