import tiktoken

from lgc.domain.schemas import Edge, EvidencePacket, EvidenceSpan, Node
from lgc.query.prune import strict_prune


def estimate_tokens(text: str) -> int:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def build_evidence_packet(
    query: str,
    nodes: list[Node],
    edges: list[Edge],
    max_tokens: int,
    metadata: dict[str, object] | None = None,
) -> EvidencePacket:
    nodes = [_compact_node(node) for node in nodes]
    edges = [_compact_edge(edge) for edge in edges]
    selected_nodes, selected_edges, used_tokens = strict_prune(query, nodes, edges, max_tokens)

    return EvidencePacket(
        query=query,
        nodes=selected_nodes,
        edges=selected_edges,
        token_budget=max_tokens,
        metadata={**(metadata or {}), "estimated_tokens": used_tokens},
    )


def _compact_node(node: Node) -> Node:
    return node.model_copy(
        update={
            "support": [_compact_span(span) for span in node.support[:3]],
            "support_node_ids": node.support_node_ids[:12],
            "metadata": _compact_metadata(node.metadata),
        }
    )


def _compact_edge(edge: Edge) -> Edge:
    return edge.model_copy(
        update={
            "support": [_compact_span(span) for span in edge.support[:2]],
            "support_node_ids": edge.support_node_ids[:12],
            "metadata": _compact_metadata(edge.metadata),
        }
    )


def _compact_span(span: EvidenceSpan) -> EvidenceSpan:
    return EvidenceSpan(
        artifact_id=span.artifact_id,
        path=span.path,
        start_line=span.start_line,
        end_line=span.end_line,
        start_col=span.start_col,
        end_col=span.end_col,
        snippet=None,
    )


def _compact_metadata(metadata: dict[str, object]) -> dict[str, object]:
    keep = {
        "kind",
        "path",
        "paths",
        "summary",
        "summary_text",
        "importance_score",
        "file_count",
        "symbol_count",
        "class_count",
        "function_count",
        "method_count",
        "import_count",
        "community",
        "rank",
        "name",
        "qualified_name",
        "url",
        "marker",
    }
    compact: dict[str, object] = {}
    for key, value in metadata.items():
        if key not in keep:
            continue
        if isinstance(value, str):
            compact[key] = value[:240]
        elif isinstance(value, list):
            compact[key] = value[:12]
        else:
            compact[key] = value
    return compact
