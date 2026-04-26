import json
from lgc.benchmark.multi_run import run_multi_benchmark

def test_run_multi_benchmark_with_questions(tmp_path):
    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "repo2"
    repo1.mkdir()
    repo2.mkdir()
    
    # Create simple python files
    (repo1 / "main.py").write_text("def hello(): pass")
    (repo2 / "main.py").write_text("def world(): pass")
    
    # Create question files
    q1 = [{"question": "where is hello", "expected_nodes": ["hello"]}]
    (repo1 / "benchmark_questions.json").write_text(json.dumps(q1))
    
    q2 = [{"question": "where is world", "expected_nodes": ["world"]}]
    (repo2 / "benchmark_questions.json").write_text(json.dumps(q2))
    
    result = run_multi_benchmark([str(repo1), str(repo2)])
    
    assert len(result["reports"]) == 2
    assert result["reports"][0]["repo_path"] == str(repo1)
    assert result["reports"][1]["repo_path"] == str(repo2)
    assert "consistency" in result["reports"][0]
    
def test_run_multi_benchmark_without_questions(tmp_path):
    repo1 = tmp_path / "repo1"
    repo1.mkdir()
    (repo1 / "main.py").write_text("def hello(): pass")
    
    result = run_multi_benchmark([str(repo1)])
    
    assert len(result["reports"]) == 1
    assert result["reports"][0]["repo_path"] == str(repo1)
    assert result["reports"][0]["consistency"] is None
