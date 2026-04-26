from lgc.benchmark.baseline import (
    BaselineResult,
    file_level_keyword_baseline,
    keyword_chunk_baseline,
    raw_context_baseline,
)


def test_raw_context_baseline_returns_total_repo_tokens(tmp_path) -> None:
    (tmp_path / "app.py").write_text("def main():\n    print('hello')\n", encoding="utf-8")
    (tmp_path / "utils.py").write_text("def helper():\n    return 1\n", encoding="utf-8")

    result = raw_context_baseline(tmp_path)

    assert isinstance(result, BaselineResult)
    assert result.tokens > 0
    assert result.chunk_count == 2


def test_keyword_chunk_top5_returns_valid_result(tmp_path) -> None:
    (tmp_path / "auth.py").write_text("def login_user():\n    return True\n", encoding="utf-8")
    (tmp_path / "db.py").write_text("def connect_db():\n    return None\n", encoding="utf-8")

    result = keyword_chunk_baseline(tmp_path, "where is login_user", top_k=5)

    assert isinstance(result, BaselineResult)
    assert result.tokens > 0
    assert result.chunk_count <= 5


def test_keyword_chunk_top10_returns_more_than_top5(tmp_path) -> None:
    for i in range(15):
        (tmp_path / f"mod_{i}.py").write_text(
            f"def func_{i}():\n    return {i}\n\ndef search():\n    pass\n",
            encoding="utf-8",
        )

    top5 = keyword_chunk_baseline(tmp_path, "search func", top_k=5)
    top10 = keyword_chunk_baseline(tmp_path, "search func", top_k=10)

    assert top10.tokens >= top5.tokens
    assert top10.chunk_count >= top5.chunk_count


def test_file_level_keyword_baseline_returns_valid_result(tmp_path) -> None:
    (tmp_path / "router.py").write_text(
        "class Router:\n    def route(self):\n        pass\n",
        encoding="utf-8",
    )
    (tmp_path / "utils.py").write_text("def helper():\n    return 1\n", encoding="utf-8")

    result = file_level_keyword_baseline(tmp_path, "route Router", top_k=3)

    assert isinstance(result, BaselineResult)
    assert result.tokens > 0
    assert result.chunk_count <= 3


def test_file_level_returns_fewer_tokens_than_raw(tmp_path) -> None:
    for i in range(10):
        (tmp_path / f"mod_{i}.py").write_text(
            f"def func_{i}():\n    return {i}\n" * 10,
            encoding="utf-8",
        )

    raw = raw_context_baseline(tmp_path)
    file_level = file_level_keyword_baseline(tmp_path, "func_0", top_k=3)

    assert file_level.tokens < raw.tokens
