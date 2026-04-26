import json
from collections import defaultdict
from pathlib import Path

from lgc.benchmark.baseline import (
    file_level_keyword_baseline,
    keyword_chunk_baseline,
    naive_rag_baseline,
    raw_context_baseline,
)
from lgc.benchmark.datasets import load_local_repo
from lgc.benchmark.questions import BenchmarkQuestion, evaluate_answer, load_questions
from lgc.benchmark.tokens import estimate_tokens
from lgc.pipeline import build_project, query_project
from lgc.storage.paths import ArtifactPaths


def run_benchmark(root: Path, questions_path: Path | None = None, max_tokens: int = 2048) -> dict[str, object]:
    root = Path(root).resolve()
    paths = ArtifactPaths(root)
    paths.ensure_out_dir()
    build_project(root)
    dataset = load_local_repo(root)
    questions = _questions(root, questions_path)

    results = _run_questions(root, questions, dataset.raw_tokens, max_tokens)
    baselines = _run_baselines(root, questions, dataset.raw_tokens)
    consistency = _run_consistency(root, questions, max_tokens, runs=3)
    by_difficulty = _aggregate_by_difficulty(results)

    avg_recall = _average([r["recall"] for r in results])
    avg_precision = _average([r["precision"] for r in results])
    avg_evidence_tokens = _average([r["evidence_tokens"] for r in results])

    diagnostics = _aggregate_diagnostics(results)

    report = {
        "dataset": str(root),
        "file_count": dataset.file_count,
        "line_count": dataset.line_count,
        "raw_tokens": dataset.raw_tokens,
        "question_count": len(questions),
        "lgc_tokens": avg_evidence_tokens,
        "compression": _ratio(dataset.raw_tokens, avg_evidence_tokens),
        "recall": round(avg_recall, 4),
        "precision": round(avg_precision, 4),
        "by_difficulty": by_difficulty,
        "baselines": baselines,
        "consistency": consistency,
        "diagnostics": diagnostics,
        "questions": results,
    }
    paths.benchmark_report.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def _run_questions(
    root: Path,
    questions: list[BenchmarkQuestion],
    raw_tokens: int,
    max_tokens: int,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for question in questions:
        packet = query_project(root, question.question, max_tokens=max_tokens)
        packet_dump = packet.model_dump(mode="json")
        if "trace" in packet_dump.get("metadata", {}):
            del packet_dump["metadata"]["trace"]
        evidence_tokens = estimate_tokens(json.dumps(packet_dump, sort_keys=True))
        metrics = evaluate_answer(packet, question.expected_nodes, question.expected_layers)
        baseline = naive_rag_baseline(root, question.question)
        expected_count = len(question.expected_nodes) + len(question.expected_layers)
        candidates_before = packet.metadata.get("candidates_before_filter", 0)
        candidates_after = packet.metadata.get("candidates_after_filter", 0)
        results.append(
            {
                "question": question.question,
                "type": question.type,
                "difficulty": question.difficulty,
                "evidence_tokens": evidence_tokens,
                "compression": _ratio(raw_tokens, evidence_tokens),
                "recall": metrics["recall"],
                "precision": metrics["precision"],
                "baseline_tokens": baseline.tokens,
                "returned_count": len(packet.nodes),
                "expected_count": expected_count,
                "matched_count": metrics["matched_count"],
                "candidates_before_filter": candidates_before,
                "candidates_after_filter": candidates_after,
                "noise_filtered": max(0, int(candidates_before) - int(candidates_after)),
                "trace": packet.metadata.get("trace"),
                "expected_nodes": question.expected_nodes,
                "expected_layers": question.expected_layers,
            }
        )
    return results


def _run_baselines(
    root: Path,
    questions: list[BenchmarkQuestion],
    raw_tokens: int,
) -> dict[str, dict[str, object]]:
    raw = raw_context_baseline(root)

    top5_tokens: list[int] = []
    top10_tokens: list[int] = []
    file_level_tokens: list[int] = []
    for question in questions:
        top5_tokens.append(keyword_chunk_baseline(root, question.question, top_k=5).tokens)
        top10_tokens.append(keyword_chunk_baseline(root, question.question, top_k=10).tokens)
        file_level_tokens.append(file_level_keyword_baseline(root, question.question).tokens)

    return {
        "raw_context": {
            "avg_tokens": raw.tokens,
            "compression": _ratio(raw_tokens, raw.tokens),
        },
        "keyword_chunk_top5": {
            "avg_tokens": round(_average(top5_tokens)),
            "compression": _ratio(raw_tokens, _average(top5_tokens)),
        },
        "keyword_chunk_top10": {
            "avg_tokens": round(_average(top10_tokens)),
            "compression": _ratio(raw_tokens, _average(top10_tokens)),
        },
        "file_level_keyword": {
            "avg_tokens": round(_average(file_level_tokens)),
            "compression": _ratio(raw_tokens, _average(file_level_tokens)),
        },
    }


def _run_consistency(
    root: Path,
    questions: list[BenchmarkQuestion],
    max_tokens: int,
    runs: int = 3,
) -> dict[str, object]:
    """Run the full question set multiple times and check for identical results."""
    all_runs: list[list[list[str]]] = []
    for _run_index in range(runs):
        run_node_ids: list[list[str]] = []
        for question in questions:
            packet = query_project(root, question.question, max_tokens=max_tokens)
            node_ids = sorted(node.id for node in packet.nodes)
            run_node_ids.append(node_ids)
        all_runs.append(run_node_ids)

    identical_questions = 0
    for q_index in range(len(questions)):
        reference = all_runs[0][q_index]
        if all(all_runs[r][q_index] == reference for r in range(1, runs)):
            identical_questions += 1

    return {
        "runs": runs,
        "identical_questions": identical_questions,
        "total_questions": len(questions),
        "consistency_score": round(identical_questions / max(1, len(questions)), 4),
    }


def _aggregate_by_difficulty(results: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for result in results:
        groups[str(result["difficulty"])].append(result)

    aggregated: dict[str, dict[str, object]] = {}
    for difficulty in ("easy", "medium", "hard"):
        group = groups.get(difficulty, [])
        if not group:
            continue
        aggregated[difficulty] = {
            "count": len(group),
            "recall": round(_average([float(r["recall"]) for r in group]), 4),
            "precision": round(_average([float(r["precision"]) for r in group]), 4),
            "avg_evidence_tokens": round(_average([float(r["evidence_tokens"]) for r in group])),
            "avg_compression": _ratio_avg([r["compression"] for r in group]),
        }
    return aggregated


def _aggregate_diagnostics(results: list[dict[str, object]]) -> dict[str, object]:
    if not results:
        return {}
    return {
        "avg_returned_candidates": round(_average([float(r.get("returned_count", 0)) for r in results]), 1),
        "avg_expected_count": round(_average([float(r.get("expected_count", 0)) for r in results]), 1),
        "avg_matched_count": round(_average([float(r.get("matched_count", 0)) for r in results]), 1),
        "avg_noise_filtered": round(_average([float(r.get("noise_filtered", 0)) for r in results]), 1),
        "avg_candidates_before_filter": round(
            _average([float(r.get("candidates_before_filter", 0)) for r in results]), 1,
        ),
    }


def _questions(root: Path, questions_path: Path | None) -> list[BenchmarkQuestion]:
    selected = questions_path or root / "benchmark_questions.json"
    if selected.exists():
        return load_questions(selected)
    return [
        BenchmarkQuestion(
            question="describe system architecture",
            expected_layers=["L3", "L2"],
            type="overview",
        )
    ]


def _average(values: list[float] | list[int]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _ratio(raw_tokens: int, target_tokens: float) -> float | None:
    if target_tokens == 0:
        return None
    return round(raw_tokens / target_tokens, 2)


def _ratio_avg(ratios: list[object]) -> float | None:
    valid = [float(r) for r in ratios if r is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)
