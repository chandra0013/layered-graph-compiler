from lgc.benchmark.datasets import create_scaled_repo, load_local_repo


def test_load_local_repo_counts_files_lines_and_tokens(tmp_path) -> None:
    (tmp_path / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Notes\n\nhello\n", encoding="utf-8")

    dataset = load_local_repo(tmp_path)

    assert dataset.file_count == 2
    assert dataset.line_count == 5
    assert dataset.raw_tokens > 0


def test_create_scaled_repo_can_make_large_dataset(tmp_path) -> None:
    create_scaled_repo(tmp_path, file_count=25)

    dataset = load_local_repo(tmp_path)

    assert dataset.file_count == 26
    assert dataset.line_count >= 125
