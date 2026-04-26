import json
from pathlib import Path

from lgc.domain.schemas import Edge, EvidencePacket, Node
from lgc.storage.paths import ArtifactPaths


L0_NODES = "nodes_l0.json"
L0_EDGES = "edges_l0.json"
L1_NODES = "nodes_l1.json"
L2_NODES = "nodes_l2.json"
L3_NODES = "nodes_l3.json"
GRAPH_L0 = "graph_l0.json"
EVIDENCE_PACKET = "evidence_packet.json"


def write_nodes(path: Path, nodes: list[Node]) -> None:
    _write_json(path, [node.model_dump(mode="json") for node in nodes])


def read_nodes(path: Path) -> list[Node]:
    return [Node.model_validate(payload) for payload in _read_json(path)]


def write_edges(path: Path, edges: list[Edge]) -> None:
    _write_json(path, [edge.model_dump(mode="json") for edge in edges])


def read_edges(path: Path) -> list[Edge]:
    return [Edge.model_validate(payload) for payload in _read_json(path)]


def write_packet(path: Path, packet: EvidencePacket) -> None:
    _write_json(path, packet.model_dump(mode="json"))


def all_nodes(root: Path) -> list[Node]:
    paths = ArtifactPaths(root)
    nodes: list[Node] = []
    for path in [paths.nodes_l0, paths.nodes_l1, paths.nodes_l2, paths.nodes_l3]:
        if path.exists():
            nodes.extend(read_nodes(path))
    return nodes


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))
