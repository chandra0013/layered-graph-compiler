import html
import json
from pathlib import Path

from lgc.storage.paths import ArtifactPaths


LAYER_COLORS = {
    "L0": "#9ca3af",
    "L1": "#2563eb",
    "L2": "#f97316",
    "L3": "#16a34a",
}


class HtmlGraphExporter:
    def export(self, root: Path) -> Path:
        root = Path(root).resolve()
        paths = ArtifactPaths(root)
        paths.ensure_out_dir()
        nodes = self._load_nodes(root)
        edges = self._load_edges(root)
        paths.graph_html.write_text(self._render_html(nodes, edges), encoding="utf-8")
        return paths.graph_html

    def _load_nodes(self, root: Path) -> list[dict]:
        paths = ArtifactPaths(root)
        payloads: list[dict] = []
        for path in [paths.nodes_l0, paths.nodes_l1, paths.nodes_l2, paths.nodes_l3]:
            payloads.extend(_load_json_list(path, fallback=root / path.name))
        return payloads

    def _load_edges(self, root: Path) -> list[dict]:
        paths = ArtifactPaths(root)
        return _load_json_list(paths.edges_l0, fallback=root / paths.edges_l0.name)

    def _node_to_vis(self, node: dict) -> dict:
        layer = str(node.get("layer", "L0"))
        metadata = node.get("metadata", {})
        title = "\n".join(
            [
                f"id: {node.get('id', '')}",
                f"label: {node.get('label', '')}",
                f"kind: {metadata.get('kind', '') if isinstance(metadata, dict) else ''}",
                f"layer: {layer}",
                f"truth: {node.get('truth', '')}",
                f"confidence: {node.get('confidence', '')}",
                f"metadata: {json.dumps(metadata, sort_keys=True)}",
                f"support_node_ids: {json.dumps(node.get('support_node_ids', []))}",
            ]
        )
        return {
            "id": node["id"],
            "label": str(node.get("label", node["id"]))[:80],
            "title": html.escape(title),
            "color": LAYER_COLORS.get(layer, "#6b7280"),
        }

    def _edge_to_vis(self, edge: dict) -> dict:
        return {
            "id": edge.get("id"),
            "from": edge.get("source_id"),
            "to": edge.get("target_id"),
            "label": edge.get("kind", ""),
            "arrows": "to",
        }

    def _render_html(self, nodes: list[dict], edges: list[dict]) -> str:
        vis_nodes = [self._node_to_vis(node) for node in nodes]
        node_ids = {node["id"] for node in vis_nodes}
        vis_edges = [
            self._edge_to_vis(edge)
            for edge in edges
            if edge.get("source_id") in node_ids and edge.get("target_id") in node_ids
        ]
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Layered Graph Compiler</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    body {{ margin: 0; font-family: Segoe UI, sans-serif; background: #f8fafc; color: #111827; }}
    #graph {{ width: 100vw; height: 92vh; border-top: 1px solid #d1d5db; }}
    .legend {{ display: flex; gap: 16px; align-items: center; padding: 12px 16px; font-size: 14px; }}
    .swatch {{ display: inline-block; width: 12px; height: 12px; margin-right: 6px; vertical-align: -1px; }}
  </style>
</head>
<body>
  <div class="legend">
    <strong>Layer legend</strong>
    <span><i class="swatch" style="background:{LAYER_COLORS['L0']}"></i>L0</span>
    <span><i class="swatch" style="background:{LAYER_COLORS['L1']}"></i>L1</span>
    <span><i class="swatch" style="background:{LAYER_COLORS['L2']}"></i>L2</span>
    <span><i class="swatch" style="background:{LAYER_COLORS['L3']}"></i>L3</span>
  </div>
  <div id="graph"></div>
  <script>
    const nodes = new vis.DataSet({json.dumps(vis_nodes)});
    const edges = new vis.DataSet({json.dumps(vis_edges)});
    new vis.Network(document.getElementById("graph"), {{ nodes, edges }}, {{
      nodes: {{ shape: "dot", size: 12, font: {{ size: 14 }} }},
      edges: {{ font: {{ size: 10, align: "middle" }}, smooth: true }},
      physics: {{ stabilization: true }}
    }});
  </script>
</body>
</html>
"""


def _load_json_list(path: Path, fallback: Path) -> list[dict]:
    selected = path if path.exists() else fallback
    if not selected.exists():
        return []
    payload = json.loads(selected.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else []
