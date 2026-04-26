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
        
        importance = 0.0
        if isinstance(metadata, dict):
            try:
                importance = float(metadata.get("importance_score", 0.0))
            except (ValueError, TypeError):
                importance = 0.0

        if layer == "L3":
            base_size = 30
            mass = 10
        elif layer == "L2":
            base_size = 20
            mass = 5
        elif layer == "L1":
            base_size = 15
            mass = 2
        else:
            base_size = 8
            mass = 1

        size = base_size + (importance * 10)

        return {
            "id": node["id"],
            "label": str(node.get("label", node["id"]))[:80],
            "title": html.escape(title),
            "color": LAYER_COLORS.get(layer, "#6b7280"),
            "layer": layer,
            "kind": metadata.get("kind", "") if isinstance(metadata, dict) else "",
            "size": size,
            "mass": mass,
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
    body {{ margin: 0; font-family: Segoe UI, sans-serif; background: #f8fafc; color: #111827; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
    .controls {{ padding: 12px 24px; background: white; border-bottom: 1px solid #d1d5db; display: flex; gap: 24px; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); z-index: 10; }}
    .controls label {{ font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 6px; font-weight: 500; }}
    .controls-group {{ display: flex; gap: 16px; align-items: center; border-right: 1px solid #e5e7eb; padding-right: 24px; }}
    input[type=text] {{ padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 6px; width: 250px; font-size: 14px; }}
    button {{ padding: 6px 16px; cursor: pointer; background: #2563eb; color: white; border: none; border-radius: 6px; font-weight: 500; transition: background 0.2s; }}
    button:hover {{ background: #1d4ed8; }}
    .swatch {{ display: inline-block; width: 14px; height: 14px; border-radius: 3px; }}
    #graph {{ width: 100vw; height: calc(100vh - 65px); }}
  </style>
</head>
<body>
  <div class="controls">
    <div class="controls-group">
      <strong>Layers</strong>
      <label><input type="checkbox" id="show-l0"><i class="swatch" style="background:{LAYER_COLORS['L0']}"></i> L0</label>
      <label><input type="checkbox" id="show-l1" checked><i class="swatch" style="background:{LAYER_COLORS['L1']}"></i> L1</label>
      <label><input type="checkbox" id="show-l2" checked><i class="swatch" style="background:{LAYER_COLORS['L2']}"></i> L2</label>
      <label><input type="checkbox" id="show-l3" checked><i class="swatch" style="background:{LAYER_COLORS['L3']}"></i> L3</label>
    </div>
    <div class="controls-group">
      <select id="filter-kind">
        <option value="">All Types</option>
        <option value="function">Function</option>
        <option value="class">Class</option>
        <option value="module">File/Module</option>
      </select>
    </div>
    <div class="controls-group" style="border: none;">
      <input type="text" id="search" placeholder="Search nodes...">
      <button id="reset-focus">Reset View</button>
    </div>
  </div>
  <div id="graph"></div>
  <script>
    const rawNodes = {json.dumps(vis_nodes)};
    const rawEdges = {json.dumps(vis_edges)};
    
    let showL0 = false;
    let showL1 = true;
    let showL2 = true;
    let showL3 = true;
    let searchQuery = "";
    let filterKind = "";
    let focusNodeId = null;
    let focusConnectedNodeIds = new Set();
    
    function filterData() {{
      const filteredNodes = rawNodes.filter(item => {{
        if (item.layer === "L0" && !showL0) return false;
        if (item.layer === "L1" && !showL1) return false;
        if (item.layer === "L2" && !showL2) return false;
        if (item.layer === "L3" && !showL3) return false;
        
        if (filterKind !== "" && item.kind !== filterKind) return false;
        
        if (searchQuery !== "" && !item.label.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        
        if (focusNodeId !== null) {{
          if (item.id !== focusNodeId && !focusConnectedNodeIds.has(item.id)) return false;
        }}
        return true;
      }});
      
      const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
      
      const filteredEdges = rawEdges.filter(item => {{
        if (!filteredNodeIds.has(item.from) || !filteredNodeIds.has(item.to)) return false;
        if (focusNodeId !== null) {{
          if (item.from !== focusNodeId && item.to !== focusNodeId) return false;
        }}
        return true;
      }});
      
      return {{
        nodes: new vis.DataSet(filteredNodes),
        edges: new vis.DataSet(filteredEdges)
      }};
    }}

    const container = document.getElementById("graph");
    const options = {{
      nodes: {{ shape: "dot", font: {{ size: 14 }} }},
      edges: {{ font: {{ size: 10, align: "middle" }}, smooth: false, color: {{ opacity: 0.5 }} }},
      physics: {{ 
        enabled: true,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {{ gravitationalConstant: -50, centralGravity: 0.01, springLength: 100, damping: 0.4 }},
        stabilization: {{ iterations: 50 }}
      }},
      layout: {{ improvedLayout: false }}
    }};
    
    let network = new vis.Network(container, filterData(), options);

    function updateNetwork() {{
      network.setData(filterData());
    }}

    // Focus mode
    network.on("click", function (params) {{
      if (params.nodes.length > 0) {{
        focusNodeId = params.nodes[0];
        focusConnectedNodeIds = new Set(network.getConnectedNodes(focusNodeId));
        updateNetwork();
      }} else {{
        focusNodeId = null;
        focusConnectedNodeIds.clear();
        updateNetwork();
      }}
    }});

    // Controls
    document.getElementById("show-l0").addEventListener("change", (e) => {{ showL0 = e.target.checked; updateNetwork(); }});
    document.getElementById("show-l1").addEventListener("change", (e) => {{ showL1 = e.target.checked; updateNetwork(); }});
    document.getElementById("show-l2").addEventListener("change", (e) => {{ showL2 = e.target.checked; updateNetwork(); }});
    document.getElementById("show-l3").addEventListener("change", (e) => {{ showL3 = e.target.checked; updateNetwork(); }});
    
    document.getElementById("filter-kind").addEventListener("change", (e) => {{
      filterKind = e.target.value;
      updateNetwork();
    }});
    
    document.getElementById("search").addEventListener("input", (e) => {{
      searchQuery = e.target.value;
      updateNetwork();
    }});
    
    document.getElementById("reset-focus").addEventListener("click", () => {{
      focusNodeId = null;
      focusConnectedNodeIds.clear();
      searchQuery = "";
      filterKind = "";
      document.getElementById("search").value = "";
      document.getElementById("filter-kind").value = "";
      updateNetwork();
      network.fit();
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
