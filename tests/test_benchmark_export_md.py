import json
from lgc.benchmark.export_md import export_benchmark_to_markdown
from lgc.storage.paths import ArtifactPaths

def test_export_benchmark_to_markdown(tmp_path):
    paths = ArtifactPaths(tmp_path)
    paths.ensure_out_dir()
    
    report_data = {
        "question_count": 25,
        "raw_tokens": 86500,
        "lgc_tokens": 1707,
        "compression": 50.69,
        "recall": 0.5093,
        "precision": 0.3005,
        "by_difficulty": {
            "easy": {"count": 8, "recall": 0.875, "precision": 0.6042, "avg_evidence_tokens": 1091, "avg_compression": 80.45}
        },
        "baselines": {
            "raw_context": {"avg_tokens": 86500, "compression": 1.0}
        },
        "consistency": {
            "runs": 3,
            "consistency_score": 1.0
        }
    }
    
    paths.benchmark_report.write_text(json.dumps(report_data))
    
    out_md = export_benchmark_to_markdown(tmp_path)
    
    assert out_md.exists()
    content = out_md.read_text(encoding="utf-8")
    assert "# LGC Benchmark Report" in content
    assert "86500" in content
    assert "50.69x" in content
    assert "Consistency Score: **1.0**" in content
