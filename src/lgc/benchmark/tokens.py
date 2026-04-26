import json
from pathlib import Path

import tiktoken

from lgc.ingest.manifest import walk_artifacts
from lgc.storage.paths import ArtifactPaths


def estimate_tokens(text: str) -> int:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def run_token_benchmark(root: Path) -> dict[str, object]:
    root = Path(root).resolve()
    paths = ArtifactPaths(root)
    paths.ensure_out_dir()

    raw_source_tokens = _raw_source_tokens(root)
    metrics = {
        "raw_source_tokens": raw_source_tokens,
        "l0_graph_tokens": _file_tokens(paths.graph_l0),
        "l1_tokens": _file_tokens(paths.nodes_l1),
        "l2_tokens": _file_tokens(paths.nodes_l2),
        "l3_tokens": _file_tokens(paths.nodes_l3),
        "evidence_packet_tokens": _file_tokens(paths.evidence_packet),
    }
    metrics["compression"] = {
        "raw_to_l0": _ratio(raw_source_tokens, metrics["l0_graph_tokens"]),
        "raw_to_l1": _ratio(raw_source_tokens, metrics["l1_tokens"]),
        "raw_to_l2": _ratio(raw_source_tokens, metrics["l2_tokens"]),
        "raw_to_l3": _ratio(raw_source_tokens, metrics["l3_tokens"]),
        "raw_to_evidence_packet": _ratio(raw_source_tokens, metrics["evidence_packet_tokens"]),
    }
    paths.token_benchmark.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    return metrics


def _raw_source_tokens(root: Path) -> int:
    total = 0
    for row in walk_artifacts(root):
        if row.parser_route == "binary_skip":
            continue
        try:
            total += estimate_tokens((root / row.path).read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
    return total


def _file_tokens(path: Path) -> int:
    if not path.exists():
        return 0
    return estimate_tokens(path.read_text(encoding="utf-8"))


def _ratio(raw_tokens: int, target_tokens: object) -> float | None:
    if not isinstance(target_tokens, int) or target_tokens == 0:
        return None
    return round(raw_tokens / target_tokens, 2)
