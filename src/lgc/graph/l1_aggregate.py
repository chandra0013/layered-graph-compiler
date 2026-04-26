from collections import defaultdict

from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Node


def aggregate_l1_file_summaries(l0_nodes: list[Node]) -> list[Node]:
    nodes_by_file: dict[str, list[Node]] = defaultdict(list)
    for node in l0_nodes:
        path = _path_for(node)
        if path:
            nodes_by_file[path].append(node)

    summaries: list[Node] = []
    for path, file_nodes in sorted(nodes_by_file.items()):
        counts = _counts_for(file_nodes)
        support_node_ids = sorted(node.id for node in file_nodes)
        summaries.append(
            Node(
                id=f"l1:file_summary:{path}",
                label="file_summary",
                layer=Layer.L1,
                truth=TruthLabel.INFERRED,
                confidence=1.0,
                support_node_ids=support_node_ids,
                metadata={
                    "kind": "file_summary",
                    "path": path,
                    "summary": _summary_text(path, counts),
                    **counts,
                },
            )
        )
    return summaries


def _path_for(node: Node) -> str | None:
    path = node.metadata.get("path")
    if isinstance(path, str):
        return path
    if node.support:
        return node.support[0].path
    return None


def _counts_for(nodes: list[Node]) -> dict[str, int]:
    kinds = [node.metadata.get("kind") for node in nodes]
    return {
        "symbol_count": len(nodes),
        "class_count": kinds.count("class"),
        "function_count": kinds.count("function"),
        "method_count": kinds.count("method"),
        "import_count": kinds.count("import"),
    }


def _summary_text(path: str, counts: dict[str, int]) -> str:
    return (
        f"{path}: {counts['symbol_count']} symbols, "
        f"{counts['class_count']} classes, "
        f"{counts['function_count']} functions, "
        f"{counts['method_count']} methods, "
        f"{counts['import_count']} imports."
    )
