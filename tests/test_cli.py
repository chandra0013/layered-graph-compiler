from typer.testing import CliRunner

from lgc.cli import app


def test_cli_version() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_inspect_placeholder() -> None:
    result = CliRunner().invoke(app, ["inspect", "."])

    assert result.exit_code == 0
    assert "l0_nodes" in result.output


def test_cli_build_and_query_end_to_end(tmp_path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        """
import os


class Service:
    def run(self):
        return os.getcwd()
""".lstrip(),
        encoding="utf-8",
    )

    build_result = CliRunner().invoke(app, ["build", str(tmp_path)])
    query_result = CliRunner().invoke(
        app,
        ["query", str(tmp_path), "where is Service implemented"],
    )

    assert build_result.exit_code == 0
    assert query_result.exit_code == 0
    out_dir = tmp_path / "lgc-out"
    assert (out_dir / "artifact_manifest.jsonl").exists()
    assert (out_dir / "nodes_l0.json").exists()
    assert (out_dir / "nodes_l1.json").exists()
    assert (out_dir / "nodes_l2.json").exists()
    assert (out_dir / "nodes_l3.json").exists()
    assert (out_dir / "evidence_packet.json").exists()
    assert "implementation-localization" in query_result.output


def test_cli_query_markdown_format(tmp_path) -> None:
    (tmp_path / "sample.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    CliRunner().invoke(app, ["build", str(tmp_path)])

    result = CliRunner().invoke(app, ["query", str(tmp_path), "where is helper", "--format", "markdown"])

    assert result.exit_code == 0
    assert "# Answer" in result.output
    assert "## Supporting Evidence" in result.output


def test_cli_query_default_remains_json(tmp_path) -> None:
    (tmp_path / "sample.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    CliRunner().invoke(app, ["build", str(tmp_path)])

    result = CliRunner().invoke(app, ["query", str(tmp_path), "where is helper"])

    assert result.exit_code == 0
    assert '"query": "where is helper"' in result.output
