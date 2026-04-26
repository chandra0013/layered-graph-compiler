"""Candidate scoring and noise filtering for precision optimization."""

from lgc.domain.enums import Layer
from lgc.domain.schemas import Node
from lgc.query.classify import QueryIntent


# Labels too generic to be useful as evidence — they appear everywhere
_GENERIC_LABELS = {
    "test", "main", "run", "init", "config", "data", "value", "item",
    "self", "args", "kwargs", "result", "output", "input", "index",
    "setup", "teardown", "fixture",
}

# Import-related keywords that signal a dependency query
_DEPENDENCY_TERMS = {"import", "imports", "depend", "dependency", "dependencies", "require", "package"}


def score_candidate(
    node: Node,
    terms: set[str],
    intent: QueryIntent,
    route_layers: list[Layer],
) -> float:
    """Compute a composite relevance score for a candidate node."""
    term_score = _query_term_score(node, terms)
    layer_score = _layer_priority_score(node, route_layers)
    importance = _importance_score(node)
    path_score = _support_path_score(node, terms)
    intent_score = _intent_compatibility_score(node, intent)

    return (
        term_score * 4.0
        + layer_score * 2.0
        + importance * 1.0
        + path_score * 3.0
        + intent_score * 2.0
    )


def is_noise(
    node: Node,
    terms: set[str],
    intent: QueryIntent,
    term_score: int,
    graph_distance: int,
) -> bool:
    """Return True if a node should be filtered as noise."""
    kind = node.metadata.get("kind", "")

    # Filter external_symbol nodes unless the query asks about imports/dependencies
    if kind == "external_symbol":
        if not terms & _DEPENDENCY_TERMS:
            return True

    # Filter very generic labels with zero term overlap
    if node.label.lower() in _GENERIC_LABELS and term_score == 0:
        return True

    # Filter nodes with zero query overlap and distance > 1
    if term_score == 0 and graph_distance > 1:
        return True

    # Filter low-confidence inferred nodes
    if node.truth.value == "INFERRED" and node.confidence < 0.5:
        return True

    # Filter test nodes unless query asks for tests
    is_test_node = "test" in node.id.lower() or "test" in node.label.lower()
    if is_test_node and "test" not in terms:
        return True

    # Filter granular documentation (paragraphs/headings) unless overview
    if kind in {"paragraph", "heading"} and intent != QueryIntent.OVERVIEW:
        return True

    return False


def filter_noise(
    nodes: list[Node],
    terms: set[str],
    intent: QueryIntent,
) -> tuple[list[Node], int]:
    """Filter noise nodes. Returns (kept_nodes, filtered_count)."""
    kept: list[Node] = []
    filtered = 0
    for node in nodes:
        ts = _query_term_score(node, terms)
        # graph_distance=0 for all nodes already selected — only filter by other criteria
        if is_noise(node, terms, intent, term_score=ts, graph_distance=0):
            filtered += 1
        else:
            kept.append(node)
    return kept, filtered


def adaptive_max_nodes(intent: QueryIntent) -> int:
    """Return max_nodes based on intent — tighter for implementation, wider for architecture."""
    if intent == QueryIntent.IMPLEMENTATION_LOCALIZATION:
        return 6
    if intent == QueryIntent.OVERVIEW:
        return 10
    if intent in {QueryIntent.ARCHITECTURE, QueryIntent.FLOW_TRACING}:
        return 12
    return 10


def _query_term_score(node: Node, terms: set[str]) -> int:
    """Count how many query terms appear in the node text."""
    haystack = " ".join([
        node.id, node.label,
        str(node.metadata.get("path", "")),
        str(node.metadata.get("name", "")),
        str(node.metadata.get("qualified_name", "")),
        str(node.metadata.get("summary", "")),
        str(node.metadata.get("community", "")),
    ]).lower()
    score = 0
    for term in terms:
        if term in haystack:
            score += 1
        elif len(term) >= 5 and term[:5] in haystack:
            score += 1
    return score


def _layer_priority_score(node: Node, route_layers: list[Layer]) -> float:
    """Higher score for layers that the route prefers."""
    if node.layer not in route_layers:
        return 0.0
    position = route_layers.index(node.layer)
    return (len(route_layers) - position) / len(route_layers)


def _importance_score(node: Node) -> float:
    """Normalize importance_score from metadata."""
    raw = node.metadata.get("importance_score")
    if isinstance(raw, int | float):
        return min(float(raw), 10.0) / 10.0
    return 0.0


def _support_path_score(node: Node, terms: set[str]) -> float:
    """Score based on whether support paths match query terms."""
    paths_text = " ".join(span.path for span in node.support).lower()
    metadata_paths = node.metadata.get("paths")
    if isinstance(metadata_paths, list):
        paths_text += " " + " ".join(str(p) for p in metadata_paths).lower()
    score = 0
    for term in terms:
        if term in paths_text:
            score += 1
        elif len(term) >= 5 and term[:5] in paths_text:
            score += 1
    return min(float(score), 3.0) / 3.0


def _intent_compatibility_score(node: Node, intent: QueryIntent) -> float:
    """Higher score if node kind matches the intent."""
    kind = node.metadata.get("kind", "")
    if intent == QueryIntent.IMPLEMENTATION_LOCALIZATION:
        return 1.0 if kind in {"function", "method", "class", "module", "file_summary"} else 0.2
    if intent in {QueryIntent.ARCHITECTURE, QueryIntent.OVERVIEW}:
        return 1.0 if kind in {"community_summary", "project_overview", "file_summary"} else 0.3
    if intent == QueryIntent.FLOW_TRACING:
        return 1.0 if kind in {"function", "method", "class", "file_summary", "community_summary"} else 0.3
    return 0.5
