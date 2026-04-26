import json

from typer.testing import CliRunner

from lgc.benchmark.run import run_benchmark
from lgc.cli import app


def test_run_benchmark_writes_report(tmp_path) -> None:
    (tmp_path / "auth.py").write_text("def login_user():\n    return True\n", encoding="utf-8")
    questions = tmp_path / "benchmark_questions.json"
    questions.write_text(
        json.dumps(
            [
                {
                    "question": "where login_user",
                    "expected_nodes": ["login_user"],
                    "type": "implementation",
                    "difficulty": "easy",
                }
            ]
        ),
        encoding="utf-8",
    )

    report = run_benchmark(tmp_path, questions)

    assert (tmp_path / "lgc-out" / "benchmark_report.json").exists()
    assert report["raw_tokens"] > 0
    assert report["questions"][0]["recall"] >= 0
    assert "diagnostics" in report
    assert report["diagnostics"]["avg_returned_candidates"] > 0
    assert "returned_count" in report["questions"][0]
    assert "expected_count" in report["questions"][0]
    assert "matched_count" in report["questions"][0]


def test_report_contains_by_difficulty(tmp_path) -> None:
    (tmp_path / "auth.py").write_text("def login_user():\n    return True\n", encoding="utf-8")
    questions = tmp_path / "benchmark_questions.json"
    questions.write_text(
        json.dumps(
            [
                {
                    "question": "where login_user",
                    "expected_nodes": ["login_user"],
                    "type": "implementation",
                    "difficulty": "easy",
                },
                {
                    "question": "describe system architecture",
                    "expected_layers": ["L3"],
                    "type": "overview",
                    "difficulty": "hard",
                },
            ]
        ),
        encoding="utf-8",
    )

    report = run_benchmark(tmp_path, questions)

    assert "by_difficulty" in report
    assert "easy" in report["by_difficulty"]
    assert "hard" in report["by_difficulty"]
    easy = report["by_difficulty"]["easy"]
    assert "recall" in easy
    assert "precision" in easy
    assert "count" in easy
    assert "avg_evidence_tokens" in easy


def test_report_contains_baselines(tmp_path) -> None:
    (tmp_path / "auth.py").write_text("def login_user():\n    return True\n", encoding="utf-8")
    questions = tmp_path / "benchmark_questions.json"
    questions.write_text(
        json.dumps(
            [{"question": "where login_user", "expected_nodes": ["login_user"], "type": "implementation"}]
        ),
        encoding="utf-8",
    )

    report = run_benchmark(tmp_path, questions)

    assert "baselines" in report
    assert "raw_context" in report["baselines"]
    assert "keyword_chunk_top5" in report["baselines"]
    assert "keyword_chunk_top10" in report["baselines"]
    assert "file_level_keyword" in report["baselines"]
    for _name, entry in report["baselines"].items():
        assert "avg_tokens" in entry
        assert "compression" in entry


def test_report_contains_consistency(tmp_path) -> None:
    (tmp_path / "auth.py").write_text("def login_user():\n    return True\n", encoding="utf-8")
    questions = tmp_path / "benchmark_questions.json"
    questions.write_text(
        json.dumps(
            [{"question": "where login_user", "expected_nodes": ["login_user"], "type": "implementation"}]
        ),
        encoding="utf-8",
    )

    report = run_benchmark(tmp_path, questions)

    assert "consistency" in report
    consistency = report["consistency"]
    assert consistency["runs"] == 3
    assert consistency["consistency_score"] == 1.0
    assert consistency["identical_questions"] == consistency["total_questions"]


def test_run_benchmark_cli_works(tmp_path) -> None:
    (tmp_path / "auth.py").write_text("def login_user():\n    return True\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["run-benchmark", str(tmp_path)])

    assert result.exit_code == 0
    assert "benchmark_report" in result.output
