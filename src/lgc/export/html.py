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

    def _edge_to_vis(self, edge: dict, node_layers: dict) -> dict:
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        return {
            "id": edge.get("id"),
            "from": source_id,
            "to": target_id,
            "label": edge.get("kind", ""),
            "layer": edge.get("layer", "L0"),
            "kind": edge.get("kind", ""),
            "fromLayer": node_layers.get(source_id, "L0"),
            "toLayer": node_layers.get(target_id, "L0"),
            "arrows": "to",
        }

    def _render_html(self, nodes: list[dict], edges: list[dict]) -> str:
        import math
        vis_nodes = [self._node_to_vis(node) for node in nodes]
        node_ids = {node["id"] for node in vis_nodes}
        node_layers = {node["id"]: node["layer"] for node in vis_nodes}
        vis_edges = [
            self._edge_to_vis(edge, node_layers)
            for edge in edges
            if edge.get("source_id") in node_ids and edge.get("target_id") in node_ids
        ]
        
        # Inject hierarchy edges for L1->L0, L2->L1, L3->L2
        for node in nodes:
            parent_id = node["id"]
            if parent_id not in node_ids:
                continue
            parent_layer = str(node.get("layer", "L0"))
            if parent_layer == "L0":
                continue
                
            for child_id in node.get("support_node_ids", []):
                if child_id in node_ids:
                    vis_edges.append({
                        "id": f"{parent_id}_hierarchy_{child_id}",
                        "from": parent_id,
                        "to": child_id,
                        "label": "contains",
                        "layer": parent_layer,
                        "fromLayer": parent_layer,
                        "toLayer": node_layers.get(child_id, "L0"),
                        "kind": "hierarchy",
                        "arrows": "to",
                    })

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
    input[type=text] {{ padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 6px; width: 200px; font-size: 14px; }}
    button {{ padding: 6px 16px; cursor: pointer; background: #2563eb; color: white; border: none; border-radius: 6px; font-weight: 500; transition: background 0.2s; }}
    button:hover {{ background: #1d4ed8; }}
    #arch-mode {{ background: #f97316; }}
    #arch-mode:hover {{ background: #ea580c; }}
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
      <button id="arch-mode">Architecture View</button>
    </div>
  </div>
  <div id="graph"></div>
  <script>
    const rawNodes = {json.dumps(vis_nodes)};
    const rawEdges = {json.dumps(vis_edges)};
    
    function assignHierarchicalPositions(nodesArray, edgesArray) {{
      const L3 = nodesArray.filter(n => n.layer === "L3");
      const L2 = nodesArray.filter(n => n.layer === "L2");
      const L1 = nodesArray.filter(n => n.layer === "L1");

      // 1. Center L3
      L3.forEach((node) => {{
        node.x = 0;
        node.y = 0;
        node.fixed = true;
      }});

      // 2. Place L2 in circle around center
      const radiusL2 = 300;
      L2.forEach((node, i) => {{
        const angle = (2 * Math.PI * i) / Math.max(1, L2.length);
        node.x = radiusL2 * Math.cos(angle);
        node.y = radiusL2 * Math.sin(angle);
      }});

      // 3. Place L1 around their nearest L2 parent
      const radiusL1 = 120;
      L1.forEach((node) => {{
        const parentEdge = edgesArray.find(e => e.to === node.id && e.fromLayer === "L2");
        if (parentEdge) {{
          const parent = nodesArray.find(n => n.id === parentEdge.from);
          if (parent && parent.x !== undefined) {{
            const angle = Math.random() * 2 * Math.PI;
            node.x = parent.x + radiusL1 * Math.cos(angle);
            node.y = parent.y + radiusL1 * Math.sin(angle);
          }}
        }}
      }});
    }}
    
    assignHierarchicalPositions(rawNodes, rawEdges);
    
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
      
      const filteredEdges = [];
      for (const item of rawEdges) {{
        if (!filteredNodeIds.has(item.from) || !filteredNodeIds.has(item.to)) continue;
        if (focusNodeId !== null && item.from !== focusNodeId && item.to !== focusNodeId) continue;
        
        let formattedEdge = {{...item}};
        
        // Hide L0 internal noise explicitly
        if (item.layer === "L0" && item.kind !== "hierarchy") {{
          formattedEdge.hidden = true;
        }}
        
        // Style hierarchy connections
        if (item.fromLayer === "L2" || item.toLayer === "L2") {{
          formattedEdge.width = 2;
          formattedEdge.color = {{ color: "#666666", opacity: 0.8 }};
        }} else if (item.fromLayer === "L3" || item.toLayer === "L3") {{
          formattedEdge.width = 3;
          formattedEdge.color = {{ color: "#333333", opacity: 1.0 }};
        }} else {{
          formattedEdge.width = 1;
          formattedEdge.color = {{ color: "#c8c8c8", opacity: 0.4 }};
        }}
        
        filteredEdges.push(formattedEdge);
      }}
      
      return {{
        nodes: new vis.DataSet(filteredNodes),
        edges: new vis.DataSet(filteredEdges)
      }};
    }}

    const container = document.getElementById("graph");
    const options = {{
      nodes: {{ shape: "dot", font: {{ size: 14 }} }},
      edges: {{ font: {{ size: 10, align: "middle" }}, smooth: false }},
      interaction: {{ hover: true, tooltipDelay: 100 }},
      physics: {{ 
        enabled: true,
        solver: "forceAtlas2Based",
        forceAtlas2Based: {{ gravitationalConstant: -30, centralGravity: 0.005, springLength: 120, springConstant: 0.05, damping: 0.4 }},
        stabilization: {{ iterations: 100 }}
      }},
      layout: {{ improvedLayout: false }}
    }};
    
    let network = new vis.Network(container, filterData(), options);

    function updateNetwork() {{
      network.setData(filterData());
    }}

    network.once("stabilizationIterationsDone", function() {{
      const l3Node = rawNodes.find(n => n.layer === "L3");
      if (l3Node) {{
        network.focus(l3Node.id, {{ scale: 1.2, animation: true }});
      }}
    }});

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
    
    document.getElementById("arch-mode").addEventListener("click", () => {{
      showL0 = false;
      showL1 = false;
      showL2 = true;
      showL3 = true;
      document.getElementById("show-l0").checked = false;
      document.getElementById("show-l1").checked = false;
      document.getElementById("show-l2").checked = true;
      document.getElementById("show-l3").checked = true;
      updateNetwork();
      const l3Node = rawNodes.find(n => n.layer === "L3");
      if (l3Node) {{
        network.focus(l3Node.id, {{ scale: 1.5, animation: true }});
      }} else {{
        network.fit();
      }}
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
