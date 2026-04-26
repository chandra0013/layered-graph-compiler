from pathlib import PurePosixPath

import networkx as nx

from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Node


def aggregate_l2_communities(l1_nodes: list[Node]) -> list[Node]:
    graph = nx.Graph()
    path_by_id = {node.id: str(node.metadata.get("path", "")) for node in l1_nodes}

    for node in l1_nodes:
        graph.add_node(node.id)

    ids = list(path_by_id)
    for index, left_id in enumerate(ids):
        for right_id in ids[index + 1 :]:
            if _community_key(path_by_id[left_id]) == _community_key(path_by_id[right_id]):
                graph.add_edge(left_id, right_id)

    communities: list[Node] = []
    for index, component in enumerate(nx.connected_components(graph), start=1):
        support_node_ids = sorted(component)
        paths = sorted(path_by_id[node_id] for node_id in support_node_ids)
        community_name = _community_key(paths[0]) if paths else f"community-{index}"
        communities.append(
            Node(
                id=f"l2:community:{index}:{community_name}",
                label=community_name,
                layer=Layer.L2,
                truth=TruthLabel.INFERRED,
                confidence=1.0,
                support_node_ids=support_node_ids,
                metadata={
                    "kind": "community_summary",
                    "community": community_name,
                    "file_count": len(paths),
                    "paths": paths,
                    "summary": f"{community_name}: {len(paths)} file summaries.",
                },
            )
        )
    return communities


def _community_key(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) <= 1:
        return "root"
    if parts[0] in {"src", "tests"} and len(parts) > 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]
