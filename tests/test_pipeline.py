from lgc.pipeline import build_project, inspect_project, query_project


def test_build_project_writes_all_core_artifacts(tmp_path) -> None:
    (tmp_path / "app.py").write_text(
        """
def main():
    print("hello")
""".lstrip(),
        encoding="utf-8",
    )

    counts = build_project(tmp_path)
    inspected = inspect_project(tmp_path)

    assert counts["l0_nodes"] >= 3
    assert counts["l0_edges"] >= 2
    assert counts["l1_nodes"] == 1
    assert counts["l2_nodes"] == 1
    assert counts["l3_nodes"] == 1
    assert (tmp_path / "lgc-out" / "artifact_manifest.jsonl").exists()
    assert inspected["manifest"] is True
    assert inspected["l3_nodes"] == 1
    assert inspected["validation_report"] is True


def test_query_project_returns_evidence_packet(tmp_path) -> None:
    (tmp_path / "service.py").write_text(
        """
class Service:
    def run(self):
        return helper()


def helper():
    return 1
""".lstrip(),
        encoding="utf-8",
    )
    build_project(tmp_path)

    packet = query_project(tmp_path, "where is Service implemented", max_tokens=4096)

    assert packet.metadata["intent"] == "implementation-localization"
    assert packet.nodes
    assert any("service.py" in str(node.metadata) for node in packet.nodes)


def test_build_project_merges_shared_external_symbol_nodes(tmp_path) -> None:
    (tmp_path / "a.py").write_text("def a():\n    print('a')\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("def b():\n    print('b')\n", encoding="utf-8")

    counts = build_project(tmp_path)

    assert counts["l0_nodes"] == 5
