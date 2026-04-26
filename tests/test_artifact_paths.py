from lgc.storage.paths import ArtifactPaths


def test_artifact_paths_point_to_lgc_out(tmp_path) -> None:
    paths = ArtifactPaths(tmp_path)

    assert paths.out_dir == tmp_path / "lgc-out"
    assert paths.nodes_l0 == tmp_path / "lgc-out" / "nodes_l0.json"
    assert paths.benchmark_report == tmp_path / "lgc-out" / "benchmark_report.json"
    assert paths.validation_report == tmp_path / "lgc-out" / "validation_report.json"


def test_artifact_paths_ensure_out_dir(tmp_path) -> None:
    paths = ArtifactPaths(tmp_path)

    assert not paths.out_dir.exists()
    assert paths.ensure_out_dir() == paths.out_dir
    assert paths.out_dir.exists()
