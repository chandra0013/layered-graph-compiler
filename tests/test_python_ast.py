from lgc.extract.python_ast import extract_python_ast


def test_extract_python_ast_finds_symbols_and_calls(tmp_path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        '''
"""Module docs."""

import os
from collections import defaultdict


class Service:
    """Service docs."""

    def run(self):
        """Run docs."""
        print(os.getcwd())


def helper():
    return defaultdict(list)
'''.lstrip(),
        encoding="utf-8",
    )

    nodes, edges = extract_python_ast(source)
    labels = {node.label for node in nodes}
    edge_kinds = {edge.kind for edge in edges}

    assert "sample" in labels
    assert "os" in labels
    assert "collections.defaultdict" in labels
    assert "Service" in labels
    assert "Service.run" in labels
    assert "helper" in labels
    assert "print" in labels
    assert "os.getcwd" in labels
    assert "defaultdict" in labels
    assert {"IMPORTS", "CONTAINS", "CALLS"} <= edge_kinds
    assert all(node.support for node in nodes)
    assert all(edge.support for edge in edges)


def test_extract_python_ast_preserves_docstrings(tmp_path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        '''
"""Module docs."""

def helper():
    """Helper docs."""
    return 1
'''.lstrip(),
        encoding="utf-8",
    )

    nodes, _edges = extract_python_ast(source)
    metadata_by_label = {node.label: node.metadata for node in nodes}

    assert metadata_by_label["sample"]["docstring"] == "Module docs."
    assert metadata_by_label["helper"]["docstring"] == "Helper docs."
