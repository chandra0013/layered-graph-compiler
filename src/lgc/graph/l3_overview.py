from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Node


def aggregate_l3_overview(l2_nodes: list[Node], cap: int = 32) -> list[Node]:
    ranked = sorted(
        l2_nodes,
        key=lambda node: (
            int(node.metadata.get("file_count", 0)),
            len(node.support_node_ids),
            node.id,
        ),
        reverse=True,
    )

    overview_nodes: list[Node] = []
    for index, node in enumerate(ranked[:cap], start=1):
        overview_nodes.append(
            Node(
                id=f"l3:overview:{index}:{node.label}",
                label=node.label,
                layer=Layer.L3,
                truth=TruthLabel.INFERRED,
                confidence=1.0,
                support_node_ids=[node.id],
                metadata={
                    "kind": "project_overview",
                    "community": node.label,
                    "rank": index,
                    "file_count": node.metadata.get("file_count", 0),
                    "summary": f"{node.label}: overview of {node.metadata.get('file_count', 0)} files.",
                },
            )
        )
    return overview_nodes
