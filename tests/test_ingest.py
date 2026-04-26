import json

from lgc.ingest.detect import parser_route_for
from lgc.ingest.hashing import sha256_file
from lgc.ingest.manifest import walk_artifacts, write_manifest


def test_sha256_file_is_content_hash(tmp_path) -> None:
    source = tmp_path / "example.txt"
    source.write_text("hello", encoding="utf-8")

    assert sha256_file(source) == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e"
        "1b161e5c1fa7425e73043362938b9824"
    )


def test_parser_route_detects_python_files(tmp_path) -> None:
    source = tmp_path / "module.py"
    source.write_text("print('ok')\n", encoding="utf-8")

    assert parser_route_for(source) == "python_ast"


def test_walk_artifacts_respects_lgcignore(tmp_path) -> None:
    (tmp_path / ".lgcignore").write_text("ignored.py\nbuild/\n", encoding="utf-8")
    (tmp_path / "kept.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "ignored.py").write_text("x = 2\n", encoding="utf-8")
    build = tmp_path / "build"
    build.mkdir()
    (build / "artifact.txt").write_text("ignored", encoding="utf-8")

    rows = walk_artifacts(tmp_path)

    assert [row.path for row in rows] == [".lgcignore", "kept.py"]


def test_write_manifest_outputs_jsonl(tmp_path) -> None:
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")

    rows = write_manifest(tmp_path)
    manifest = tmp_path / "artifact_manifest.jsonl"
    lines = manifest.read_text(encoding="utf-8").splitlines()

    assert len(rows) == 1
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["path"] == "main.py"
    assert payload["extension"] == ".py"
    assert payload["parser_route"] == "python_ast"
