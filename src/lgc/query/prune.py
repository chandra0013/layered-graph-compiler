import json

import tiktoken

from lgc.domain.enums import Layer
from lgc.domain.schemas import Edge, Node


LAYER_PRIORITY = {Layer.L3: 4, Layer.L2: 3, Layer.L1: 2, Layer.L0: 1}


def strict_prune(
    query: str,
    nodes: list[Node],
    edges: list[Edge],
    max_tokens: int,
) -> tuple[list[Node], list[Edge], int]:
    used = estimate_tokens(query)
    selected_nodes: list[Node] = []
    for node in sorted(nodes, key=_node_priority, reverse=True):
        token_cost = _fact_tokens(node)
        if used + token_cost > max_tokens:
            continue
        selected_nodes.append(node)
        used += token_cost

    selected_ids = {node.id for node in selected_nodes}
    selected_edges: list[Edge] = []
    for edge in edges:
        if edge.source_id not in selected_ids or edge.target_id not in selected_ids:
            continue
        token_cost = _fact_tokens(edge)
        if used + token_cost > max_tokens:
            continue
        selected_edges.append(edge)
        used += token_cost

    return selected_nodes, selected_edges, used


def _node_priority(node: Node) -> tuple[int, float, str]:
    return (
        LAYER_PRIORITY.get(node.layer, 0),
        float(node.metadata.get("importance_score", 0.0)),
        node.id,
    )


def _fact_tokens(fact: Node | Edge) -> int:
    return estimate_tokens(json.dumps(fact.model_dump(mode="json"), sort_keys=True))


def estimate_tokens(text: str) -> int:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, len(text) // 4)
