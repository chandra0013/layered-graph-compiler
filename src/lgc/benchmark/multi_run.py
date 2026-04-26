import json
import time
from pathlib import Path

from lgc.benchmark.run import run_benchmark
from lgc.benchmark.tokens import run_token_benchmark
from lgc.pipeline import build_project
from lgc.storage.paths import ArtifactPaths


def run_multi_benchmark(repo_paths: list[str]) -> dict[str, object]:
    results = []
    
    for repo_str in repo_paths:
        repo = Path(repo_str).resolve()
        if not repo.exists():
            continue
            
        start_time = time.time()
        
        # Build the project
        build_project(repo)
        
        build_time = time.time() - start_time
        
        paths = ArtifactPaths(repo)
        
        # Check if benchmark_questions.json exists
        questions_path = repo / "benchmark_questions.json"
        
        node_counts = {
            "L0": _count_nodes(paths.nodes_l0),
            "L1": _count_nodes(paths.nodes_l1),
            "L2": _count_nodes(paths.nodes_l2),
            "L3": _count_nodes(paths.nodes_l3),
        }
        
        if questions_path.exists():
            report = run_benchmark(repo, questions_path)
            results.append({
                "repo_path": str(repo),
                "raw_tokens": report["raw_tokens"],
                "lgc_tokens": report["lgc_tokens"],
                "compression": report["compression"],
                "build_time": round(build_time, 2),
                "node_counts": node_counts,
                "consistency": report.get("consistency", {}).get("consistency_score"),
            })
        else:
            token_metrics = run_token_benchmark(repo)
            results.append({
                "repo_path": str(repo),
                "raw_tokens": token_metrics["raw_source_tokens"],
                "lgc_tokens": token_metrics["evidence_packet_tokens"],
                "compression": token_metrics["compression"].get("raw_to_evidence_packet"),
                "build_time": round(build_time, 2),
                "node_counts": node_counts,
                "consistency": None,
            })
            
    out_dir = Path("lgc-out")
    out_dir.mkdir(exist_ok=True)
    report_path = out_dir / "multi_repo_report.json"
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    
    return {"reports": results, "output_file": str(report_path.resolve())}


def _count_nodes(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return len(data)
    except Exception:
        return 0
