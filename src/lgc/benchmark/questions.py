import json
from pathlib import Path

from pydantic import BaseModel, Field

from lgc.domain.schemas import EvidencePacket


class BenchmarkQuestion(BaseModel):
    question: str
    expected_nodes: list[str] = Field(default_factory=list)
    expected_layers: list[str] = Field(default_factory=list)
    type: str = "unknown"
    difficulty: str = "medium"


def load_questions(path: Path) -> list[BenchmarkQuestion]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [BenchmarkQuestion.model_validate(item) for item in payload]


def evaluate_answer(
    evidence_packet: EvidencePacket,
    expected_nodes: list[str] | None = None,
    expected_layers: list[str] | None = None,
) -> dict[str, float]:
    expected_nodes = expected_nodes or []
    expected_layers = expected_layers or []
    retrieved = [_node_text(node) for node in evidence_packet.nodes]
    retrieved_layers = [node.layer.value for node in evidence_packet.nodes]

    expected_total = len(expected_nodes) + len(expected_layers)
    if expected_total == 0:
        return {"recall": 1.0, "precision": 1.0}

    hits = 0
    for expected in expected_nodes:
        if any(expected.lower() in item.lower() for item in retrieved):
            hits += 1
    for layer in expected_layers:
        if layer in retrieved_layers:
            hits += 1

    relevant_retrieved = 0
    for item in retrieved:
        if any(expected.lower() in item.lower() for expected in expected_nodes):
            relevant_retrieved += 1
    for node in evidence_packet.nodes:
        if node.layer.value in expected_layers:
            relevant_retrieved += 1

    recall = hits / expected_total
    precision = relevant_retrieved / max(1, len(evidence_packet.nodes))
    return {
        "recall": round(recall, 4),
        "precision": round(min(1.0, precision), 4),
        "matched_count": hits,
    }


def _node_text(node) -> str:
    parts = [node.id, node.label, str(node.metadata)]
    # Include support_node_ids so L1/L2 nodes matching their child IDs are found
    if node.support_node_ids:
        parts.append(" ".join(node.support_node_ids))
    # Include span paths
    for span in node.support:
        parts.append(span.path)
    # Include paths from metadata if present
    paths = node.metadata.get("paths")
    if isinstance(paths, list):
        parts.extend(str(p) for p in paths)
    return " ".join(parts)
