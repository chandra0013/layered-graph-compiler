from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Node
from lgc.graph.l2_aggregate import aggregate_l2_communities
from lgc.graph.l3_overview import aggregate_l3_overview


def l1_node(path: str) -> Node:
    return Node(
        id=f"l1:file_summary:{path}",
        label="file_summary",
        layer=Layer.L1,
        truth=TruthLabel.INFERRED,
        confidence=1.0,
        support_node_ids=[f"l0:{path}"],
        metadata={"kind": "file_summary", "path": path},
    )


def test_l2_groups_l1_files_by_top_level_community() -> None:
    communities = aggregate_l2_communities(
        [
            l1_node("src/api/routes.py"),
            l1_node("src/api/models.py"),
            l1_node("src/core/compiler.py"),
        ]
    )

    by_label = {node.label: node for node in communities}

    assert set(by_label) == {"src/api", "src/core"}
    assert by_label["src/api"].support_node_ids == [
        "l1:file_summary:src/api/models.py",
        "l1:file_summary:src/api/routes.py",
    ]
    assert by_label["src/api"].metadata["file_count"] == 2


def test_l3_overview_caps_and_ranks_communities() -> None:
    l2_nodes = aggregate_l2_communities(
        [
            l1_node("src/api/a.py"),
            l1_node("src/api/b.py"),
            l1_node("src/core/c.py"),
        ]
    )

    overview = aggregate_l3_overview(l2_nodes, cap=1)

    assert len(overview) == 1
    assert overview[0].layer == Layer.L3
    assert overview[0].label == "src/api"
    assert overview[0].support_node_ids == ["l2:community:1:src/api"]
