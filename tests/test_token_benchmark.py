from typer.testing import CliRunner

from lgc.benchmark.tokens import run_token_benchmark
from lgc.benchmark import tokens
from lgc.cli import app
from lgc.pipeline import build_project, query_project


def test_token_benchmark_writes_json_and_ratios(tmp_path) -> None:
    (tmp_path / "sample.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    build_project(tmp_path)
    query_project(tmp_path, "where is helper")

    metrics = run_token_benchmark(tmp_path)

    assert (tmp_path / "lgc-out" / "token_benchmark.json").exists()
    assert metrics["raw_source_tokens"] > 0
    assert metrics["compression"]["raw_to_l1"] is not None


def test_token_benchmark_cli_works(tmp_path) -> None:
    (tmp_path / "sample.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    CliRunner().invoke(app, ["build", str(tmp_path)])

    result = CliRunner().invoke(app, ["benchmark", str(tmp_path)])

    assert result.exit_code == 0
    assert "raw_source_tokens" in result.output


def test_token_estimation_fallback(monkeypatch) -> None:
    def fail_get_encoding(_name: str):
        raise RuntimeError("missing tokenizer")

    monkeypatch.setattr(tokens.tiktoken, "get_encoding", fail_get_encoding)

    assert tokens.estimate_tokens("abcdefgh") == 2
