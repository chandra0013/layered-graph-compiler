from pathlib import Path


OUT_DIR_NAME = "lgc-out"


class ArtifactPaths:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.out_dir = self.root / OUT_DIR_NAME

    def ensure_out_dir(self) -> Path:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        return self.out_dir

    @property
    def manifest(self) -> Path:
        return self.out_dir / "artifact_manifest.jsonl"

    @property
    def nodes_l0(self) -> Path:
        return self.out_dir / "nodes_l0.json"

    @property
    def edges_l0(self) -> Path:
        return self.out_dir / "edges_l0.json"

    @property
    def graph_l0(self) -> Path:
        return self.out_dir / "graph_l0.json"

    @property
    def nodes_l1(self) -> Path:
        return self.out_dir / "nodes_l1.json"

    @property
    def nodes_l2(self) -> Path:
        return self.out_dir / "nodes_l2.json"

    @property
    def nodes_l3(self) -> Path:
        return self.out_dir / "nodes_l3.json"

    @property
    def evidence_packet(self) -> Path:
        return self.out_dir / "evidence_packet.json"

    @property
    def graph_html(self) -> Path:
        return self.out_dir / "graph.html"

    @property
    def token_benchmark(self) -> Path:
        return self.out_dir / "token_benchmark.json"

    @property
    def benchmark_report(self) -> Path:
        return self.out_dir / "benchmark_report.json"

    @property
    def validation_report(self) -> Path:
        return self.out_dir / "validation_report.json"
