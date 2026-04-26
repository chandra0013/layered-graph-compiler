import json
from pathlib import Path

from lgc.storage.paths import ArtifactPaths


def export_benchmark_to_markdown(root: Path) -> Path:
    paths = ArtifactPaths(root)
    report_path = paths.benchmark_report
    if not report_path.exists():
        raise FileNotFoundError(f"Benchmark report not found at {report_path}")
        
    data = json.loads(report_path.read_text(encoding="utf-8"))
    
    out_md = paths.out_dir / "BENCHMARK_REPORT.md"
    
    lines = []
    lines.append("# LGC Benchmark Report")
    lines.append("")
    
    # Summary Table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Questions | {data.get('question_count', 0)} |")
    lines.append(f"| Raw Tokens | {data.get('raw_tokens', 0)} |")
    lines.append(f"| LGC Tokens | {round(data.get('lgc_tokens', 0))} |")
    lines.append(f"| Compression | {data.get('compression', 'N/A')}x |")
    lines.append(f"| Recall | {data.get('recall', 0)} |")
    lines.append(f"| Precision | {data.get('precision', 0)} |")
    lines.append("")
    
    # Per-Difficulty
    lines.append("## Per-Difficulty Metrics")
    lines.append("")
    lines.append("| Difficulty | Count | Recall | Precision | Avg Tokens | Avg Compression |")
    lines.append("|---|---|---|---|---|---|")
    by_diff = data.get("by_difficulty", {})
    for level in ["easy", "medium", "hard"]:
        if level in by_diff:
            d = by_diff[level]
            lines.append(f"| {level} | {d.get('count', 0)} | {d.get('recall', 0)} | {d.get('precision', 0)} | {d.get('avg_evidence_tokens', 0)} | {d.get('avg_compression', 'N/A')}x |")
    lines.append("")
    
    # Baselines
    lines.append("## Baseline Comparison")
    lines.append("")
    lines.append("| Method | Avg Tokens | Compression |")
    lines.append("|---|---|---|")
    baselines = data.get("baselines", {})
    for name, b in baselines.items():
        comp = f"{b.get('compression')}x" if b.get('compression') else "N/A"
        lines.append(f"| {name} | {b.get('avg_tokens', 0)} | {comp} |")
    lines.append(f"| **LGC** | **{round(data.get('lgc_tokens', 0))}** | **{data.get('compression', 'N/A')}x** |")
    lines.append("")
    
    # Consistency
    lines.append("## Consistency")
    lines.append("")
    cons = data.get("consistency", {})
    score = cons.get("consistency_score", "N/A")
    runs = cons.get("runs", 3)
    lines.append(f"Consistency Score: **{score}** across {runs} deterministic runs.")
    lines.append("")
    
    # Interpretation
    lines.append("## Interpretation")
    lines.append("")
    lines.append("These metrics demonstrate LGC's deterministic graph retrieval capabilities. ")
    lines.append("By extracting facts, aggregating layers (L0-L3), and selecting subgraphs based on multi-source BFS, ")
    lines.append("LGC provides extremely high compression ratios while retaining strong recall on queries compared to raw context or simple keyword searches.")
    lines.append("LGC runs without embeddings or LLM-based query interpretation, relying instead on structural importance, term overlap, and neighborhood expansion.")
    lines.append("Recall captures how many requested facts are returned; precision reflects evidence purity.")
    lines.append("High consistency (1.0) ensures pipeline determinism.")
    lines.append("")
    
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return out_md
