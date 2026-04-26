from pathlib import Path

from lgc.agents.pipeline import run_validations
from lgc.artifacts import all_nodes, read_edges, read_nodes, write_edges, write_nodes
from lgc.config import load_config
from lgc.domain.schemas import Edge, Node
from lgc.extract.python_ast import extract_python_ast
from lgc.extract.text_docs import extract_text_document
from lgc.graph.l0_builder import build_l0_graph, export_l0_json
from lgc.graph.importance import annotate_importance
from lgc.graph.l1_aggregate import aggregate_l1_file_summaries
from lgc.graph.l2_aggregate import aggregate_l2_communities
from lgc.graph.l3_overview import aggregate_l3_overview
from lgc.ingest.manifest import ArtifactManifestRow, write_manifest
from lgc.models.ollama_client import OllamaSummaryModel
from lgc.query.route import route_query
from lgc.storage.paths import ArtifactPaths
from lgc.summarize.local_summary import LocalSummaryService
from lgc.validate.compression_guard import CompressionGuard
from lgc.validate.provenance_guard import ProvenanceGuard


def scan_project(root: Path) -> list[ArtifactManifestRow]:
    root = root.resolve()
    paths = ArtifactPaths(root)
    paths.ensure_out_dir()
    return write_manifest(root, paths.manifest)


def extract_project(root: Path) -> tuple[list[Node], list[Edge]]:
    root = root.resolve()
    paths = ArtifactPaths(root)
    paths.ensure_out_dir()
    rows = scan_project(root)
    nodes: list[Node] = []
    edges: list[Edge] = []

    for row in rows:
        if row.parser_route == "python_ast":
            extracted_nodes, extracted_edges = extract_python_ast(root / row.path, logical_path=row.path)
        elif row.parser_route == "text_docs":
            extracted_nodes, extracted_edges = extract_text_document(root / row.path, logical_path=row.path)
        else:
            continue
        nodes.extend(extracted_nodes)
        edges.extend(extracted_edges)

    nodes = _merge_duplicate_nodes(nodes)
    nodes = annotate_importance(nodes, edges)
    ProvenanceGuard().validate(nodes, edges)
    write_nodes(paths.nodes_l0, nodes)
    write_edges(paths.edges_l0, edges)
    return nodes, edges


def build_project(root: Path) -> dict[str, int]:
    root = root.resolve()
    paths = ArtifactPaths(root)
    paths.ensure_out_dir()
    l0_nodes, l0_edges = extract_project(root)
    build_l0_graph(l0_nodes, l0_edges)
    export_l0_json(l0_nodes, l0_edges, paths.graph_l0)

    l1_nodes = aggregate_l1_file_summaries(l0_nodes)
    l2_nodes = aggregate_l2_communities(l1_nodes)
    l3_nodes = aggregate_l3_overview(l2_nodes)
    l1_nodes, l2_nodes, l3_nodes = _maybe_enrich_summaries(root, l1_nodes, l2_nodes, l3_nodes)
    CompressionGuard().validate([*l1_nodes, *l2_nodes, *l3_nodes])
    validation_report = run_validations(root, l0_nodes, l0_edges, l1_nodes, l2_nodes, l3_nodes)
    if not validation_report["provenance"]["passed"]:
        raise RuntimeError("Provenance validation failed")

    write_nodes(paths.nodes_l1, l1_nodes)
    write_nodes(paths.nodes_l2, l2_nodes)
    write_nodes(paths.nodes_l3, l3_nodes)

    return {
        "l0_nodes": len(l0_nodes),
        "l0_edges": len(l0_edges),
        "l1_nodes": len(l1_nodes),
        "l2_nodes": len(l2_nodes),
        "l3_nodes": len(l3_nodes),
    }


def query_project(root: Path, question: str, max_tokens: int = 2048):
    root = root.resolve()
    paths = ArtifactPaths(root)
    if not paths.nodes_l3.exists():
        build_project(root)

    nodes = all_nodes(root)
    edges = read_edges(paths.edges_l0) if paths.edges_l0.exists() else []
    return route_query(question, nodes, edges, max_tokens=max_tokens)


def inspect_project(root: Path) -> dict[str, int | bool]:
    root = root.resolve()
    paths = ArtifactPaths(root)
    return {
        "manifest": paths.manifest.exists(),
        "l0_nodes": _count_json_list(paths.nodes_l0),
        "l0_edges": _count_json_list(paths.edges_l0),
        "l1_nodes": _count_json_list(paths.nodes_l1),
        "l2_nodes": _count_json_list(paths.nodes_l2),
        "l3_nodes": _count_json_list(paths.nodes_l3),
        "validation_report": paths.validation_report.exists(),
    }


def _count_json_list(path: Path) -> int:
    if not path.exists():
        return 0
    return len(read_nodes(path) if "nodes" in path.name else read_edges(path))


def _merge_duplicate_nodes(nodes: list[Node]) -> list[Node]:
    merged: dict[str, Node] = {}
    for node in nodes:
        existing = merged.get(node.id)
        if existing is None:
            merged[node.id] = node
            continue

        support = [*existing.support]
        known_spans = {(span.path, span.start_line, span.end_line) for span in support}
        for span in node.support:
            key = (span.path, span.start_line, span.end_line)
            if key not in known_spans:
                support.append(span)
                known_spans.add(key)

        support_node_ids = sorted({*existing.support_node_ids, *node.support_node_ids})
        metadata = {**existing.metadata}
        paths = set(metadata.get("paths", [])) if isinstance(metadata.get("paths"), list) else set()
        for span in support:
            paths.add(span.path)
        if paths:
            metadata["paths"] = sorted(paths)

        merged[node.id] = existing.model_copy(
            update={"support": support, "support_node_ids": support_node_ids, "metadata": metadata}
        )
    return list(merged.values())


def _maybe_enrich_summaries(
    root: Path,
    l1_nodes: list[Node],
    l2_nodes: list[Node],
    l3_nodes: list[Node],
) -> tuple[list[Node], list[Node], list[Node]]:
    config = load_config(root)
    if not config.models.enabled:
        return l1_nodes, l2_nodes, l3_nodes
    model = None
    if config.models.provider == "ollama":
        model = OllamaSummaryModel(
            model=config.models.model,
            base_url=config.models.base_url,
            timeout_seconds=config.models.timeout_seconds,
        )
    service = LocalSummaryService(model, enabled=model is not None)
    return (
        service.enrich_nodes(l1_nodes),
        service.enrich_nodes(l2_nodes),
        service.enrich_nodes(l3_nodes),
    )
