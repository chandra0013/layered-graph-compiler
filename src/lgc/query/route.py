from lgc.domain.enums import Layer
from lgc.domain.schemas import Edge, EvidencePacket, Node
from lgc.query.classify import QueryIntent, classify_query
from lgc.query.evidence_packet import build_evidence_packet
from lgc.query.path_select import select_path_evidence
from lgc.query.scoring import adaptive_max_nodes, filter_noise, score_candidate


ROUTES = {
    QueryIntent.OVERVIEW: [Layer.L3, Layer.L2, Layer.L1],
    QueryIntent.ARCHITECTURE: [Layer.L3, Layer.L2, Layer.L1, Layer.L0],
    QueryIntent.IMPLEMENTATION_LOCALIZATION: [Layer.L1, Layer.L0],
    QueryIntent.FLOW_TRACING: [Layer.L2, Layer.L1, Layer.L0],
    QueryIntent.RATIONALE: [Layer.L2, Layer.L1, Layer.L0],
    QueryIntent.UNKNOWN: [Layer.L3, Layer.L2, Layer.L1, Layer.L0],
}


def route_query(
    question: str,
    nodes: list[Node],
    edges: list[Edge],
    max_tokens: int = 2048,
) -> EvidencePacket:
    intent = classify_query(question)
    route_layers = ROUTES[intent]
    terms = _terms(question)

    # Score and rank candidates
    candidates = [node for node in nodes if node.layer in route_layers]
    ranked_nodes = sorted(
        candidates,
        key=lambda node: (
            score_candidate(node, terms, intent, route_layers),
            node.id,
        ),
        reverse=True,
    )
    if not ranked_nodes:
        ranked_nodes = nodes

    # Implementation: restrict to code/file nodes
    if intent == QueryIntent.IMPLEMENTATION_LOCALIZATION:
        code_nodes = [node for node in ranked_nodes if _is_code_or_file_node(node)]
        if code_nodes:
            non_external = [node for node in code_nodes if node.metadata.get("kind") != "external_symbol"]
            if non_external:
                code_nodes = non_external
            ranked_nodes = code_nodes

    # Noise filtering — pre-expansion
    ranked_nodes, _filtered_count = filter_noise(ranked_nodes, terms, intent)
    if not ranked_nodes:
        ranked_nodes = candidates[:4] or nodes[:4]

    # Capture trace information for diagnostics
    trace_info = {
        "terms": list(terms),
        "intent_classification": intent.value,
        "initial_candidates_count": len(candidates),
        "post_filter_seeds": [node.id for node in ranked_nodes],
    }

    # For architecture/flow queries, expand with neighbors + support chain
    if intent in {QueryIntent.ARCHITECTURE, QueryIntent.FLOW_TRACING, QueryIntent.UNKNOWN}:
        before_expansion = set(node.id for node in ranked_nodes)
        ranked_nodes = _expand_with_neighbors(ranked_nodes, nodes, edges, terms, max_extra=12)
        trace_info["neighbors_added"] = [n.id for n in ranked_nodes if n.id not in before_expansion]
        
        before_support = set(node.id for node in ranked_nodes)
        ranked_nodes = _expand_support_chain(ranked_nodes, nodes, max_descendants=6)
        trace_info["support_added"] = [n.id for n in ranked_nodes if n.id not in before_support]
        
        # Post-expansion noise filter to remove noisy neighbors
        ranked_nodes, _ = filter_noise(ranked_nodes, terms, intent)
        if not ranked_nodes:
            ranked_nodes = candidates[:4] or nodes[:4]
            
        trace_info["post_expansion_nodes"] = [node.id for node in ranked_nodes]

    # Adaptive node budget
    max_selected = adaptive_max_nodes(intent)
    selected_nodes, selected_edges = select_path_evidence(
        question, ranked_nodes, edges, max_nodes=max_selected,
    )
    if intent == QueryIntent.IMPLEMENTATION_LOCALIZATION:
        selected_edges = []

    trace_info["final_selected_nodes"] = [node.id for node in selected_nodes]
    
    # Optional: capture top 5 discarded nodes and their scores
    selected_ids = {node.id for node in selected_nodes}
    discarded = [node for node in ranked_nodes if node.id not in selected_ids][:5]
    trace_info["top_discarded"] = [
        {"id": node.id, "score": score_candidate(node, terms, intent, route_layers)} 
        for node in discarded
    ]
    # And top 5 selected node scores
    trace_info["top_selected_scores"] = [
        {"id": node.id, "score": score_candidate(node, terms, intent, route_layers)}
        for node in selected_nodes[:5]
    ]

    return build_evidence_packet(
        query=question,
        nodes=selected_nodes,
        edges=selected_edges,
        max_tokens=max_tokens,
        metadata={
            "intent": intent.value,
            "route_layers": [layer.value for layer in route_layers],
            "selection": "path_select",
            "candidates_before_filter": len(candidates),
            "candidates_after_filter": len(trace_info["post_filter_seeds"]),
            "trace": trace_info,
        },
    )


def _expand_with_neighbors(
    ranked_nodes: list[Node],
    all_nodes: list[Node],
    edges: list[Edge],
    terms: set[str],
    max_extra: int = 12,
) -> list[Node]:
    """Expand seed nodes by including their graph neighbors via edges."""
    node_by_id = {node.id: node for node in all_nodes}
    seed_ids = {node.id for node in ranked_nodes[:8]}
    neighbor_ids: set[str] = set()

    for edge in edges:
        if len(neighbor_ids) >= max_extra:
            break
        if edge.source_id in seed_ids and edge.target_id not in seed_ids:
            target = node_by_id.get(edge.target_id)
            if target and target.metadata.get("kind") != "external_symbol":
                neighbor_ids.add(edge.target_id)
        elif edge.target_id in seed_ids and edge.source_id not in seed_ids:
            source = node_by_id.get(edge.source_id)
            if source and source.metadata.get("kind") != "external_symbol":
                neighbor_ids.add(edge.source_id)

    # Pull in L1 file summaries for files containing seed L0 nodes
    seed_paths: set[str] = set()
    for node in ranked_nodes[:8]:
        path = node.metadata.get("path")
        if isinstance(path, str):
            seed_paths.add(path)
    for node in all_nodes:
        if node.id not in seed_ids and node.metadata.get("kind") == "file_summary":
            node_path = node.metadata.get("path")
            if isinstance(node_path, str) and node_path in seed_paths:
                neighbor_ids.add(node.id)

    existing_ids = {node.id for node in ranked_nodes}
    extra = [node_by_id[nid] for nid in neighbor_ids if nid in node_by_id and nid not in existing_ids]
    return ranked_nodes + extra


def _expand_support_chain(
    ranked_nodes: list[Node],
    all_nodes: list[Node],
    max_descendants: int = 6,
) -> list[Node]:
    """Follow support_node_ids downward from L3/L2 nodes to include top supported descendants."""
    node_by_id = {node.id: node for node in all_nodes}
    existing_ids = {node.id for node in ranked_nodes}
    descendants: list[Node] = []

    for node in ranked_nodes:
        if node.layer not in {Layer.L3, Layer.L2}:
            continue
        if len(descendants) >= max_descendants:
            break
        for support_id in node.support_node_ids:
            if support_id in existing_ids:
                continue
            supported = node_by_id.get(support_id)
            if supported is None:
                continue
            existing_ids.add(support_id)
            descendants.append(supported)
            if len(descendants) >= max_descendants:
                break
            # One more level: L2 → L1 → follow L1 support_node_ids
            for child_id in supported.support_node_ids[:3]:
                if child_id in existing_ids:
                    continue
                child = node_by_id.get(child_id)
                if child is None:
                    continue
                existing_ids.add(child_id)
                descendants.append(child)
                if len(descendants) >= max_descendants:
                    break

    return ranked_nodes + descendants


def _terms(question: str) -> set[str]:
    terms: set[str] = set()
    for part in question.lower().replace("_", " ").replace("-", " ").split():
        cleaned = part.strip(".,:;!?()[]{}\"'")
        if len(cleaned) <= 2:
            continue
        terms.add(cleaned)
        for suffix in ("tion", "sion", "ment", "ness", "ing", "ed", "er", "es", "s", "al", "ly"):
            if cleaned.endswith(suffix) and len(cleaned) > len(suffix) + 3:
                terms.add(cleaned[: -len(suffix)])
                break
    return terms


def _is_code_or_file_node(node: Node) -> bool:
    return str(node.metadata.get("kind", "")) in {
        "module",
        "class",
        "function",
        "method",
        "import",
        "file_summary",
        "external_symbol",
    }
