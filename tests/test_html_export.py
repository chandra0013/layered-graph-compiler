import json

from typer.testing import CliRunner

from lgc.cli import app
from lgc.export.html import HtmlGraphExporter


def test_html_export_creates_graph_with_legend_and_labels(tmp_path) -> None:
    out_dir = tmp_path / "lgc-out"
    out_dir.mkdir()
    (out_dir / "nodes_l0.json").write_text(
        json.dumps(
            [
                {
                    "id": "n1",
                    "label": "Example",
                    "layer": "L0",
                    "truth": "EXTRACTED",
                    "confidence": 1.0,
                    "support": [{"path": "a.py", "start_line": 1, "end_line": 1}],
                    "support_node_ids": [],
                    "metadata": {"kind": "function"},
                }
            ]
        ),
        encoding="utf-8",
    )
    (out_dir / "edges_l0.json").write_text("[]", encoding="utf-8")

    output = HtmlGraphExporter().export(tmp_path)
    html = output.read_text(encoding="utf-8")

    assert output == out_dir / "graph.html"
    assert "vis-network" in html
    assert "Example" in html
    assert "Layer legend" in html


def test_cli_visualize_command_works(tmp_path) -> None:
    (tmp_path / "sample.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    CliRunner().invoke(app, ["build", str(tmp_path)])

    result = CliRunner().invoke(app, ["visualize", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / "lgc-out" / "graph.html").exists()
