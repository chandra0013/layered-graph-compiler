from collections import defaultdict

from lgc.domain.schemas import Edge, EvidencePacket, Node


class MarkdownRenderer:
    def render(self, packet: EvidencePacket) -> str:
        sections = [
            "# Answer",
            "",
            "## Direct Answer",
            self._render_direct_answer(packet),
            "",
            "## Supporting Evidence",
            self._render_supporting_evidence(packet),
            "",
            "## Relevant Files",
            self._render_relevant_files(packet),
            "",
            "## Confidence Notes",
            self._render_confidence_notes(packet),
        ]
        return "\n".join(sections).rstrip() + "\n"

    def _render_direct_answer(self, packet: EvidencePacket) -> str:
        if not packet.nodes and not packet.edges:
            return "No supported evidence was found in the current graph."

        labels = [f"`{node.label}` (`{node.id}`)" for node in packet.nodes[:5]]
        if labels:
            return "Relevant graph evidence was found: " + ", ".join(labels) + "."
        return "Relevant edge evidence was found in the current graph."

    def _render_supporting_evidence(self, packet: EvidencePacket) -> str:
        if not packet.nodes and not packet.edges:
            return "No supported evidence was found in the current graph."

        lines: list[str] = []
        for node in packet.nodes[:10]:
            lines.append(self._node_line(node))
        for edge in packet.edges[:10]:
            lines.append(self._edge_line(edge))
        return "\n".join(lines) if lines else "No supported evidence was found in the current graph."

    def _render_relevant_files(self, packet: EvidencePacket) -> str:
        by_path: dict[str, list[str]] = defaultdict(list)
        for node in packet.nodes:
            self._collect_spans(by_path, node)
        for edge in packet.edges:
            self._collect_spans(by_path, edge)

        if not by_path:
            return "No source file spans were included in the evidence packet."

        lines: list[str] = []
        for path in sorted(by_path):
            spans = ", ".join(sorted(set(by_path[path])))
            lines.append(f"- `{path}`: {spans}")
        return "\n".join(lines)

    def _render_confidence_notes(self, packet: EvidencePacket) -> str:
        facts = [*packet.nodes, *packet.edges]
        if not facts:
            return "No confidence values were available because no evidence was found."

        values = ", ".join(f"`{fact.id}`={fact.confidence:.2f}" for fact in facts[:12])
        return f"Confidence values are copied directly from the evidence packet: {values}."

    @staticmethod
    def _node_line(node: Node) -> str:
        kind = node.metadata.get("kind", "node")
        return f"- Node `{node.id}`: label `{node.label}`, kind `{kind}`, layer `{node.layer}`, confidence `{node.confidence:.2f}`."

    @staticmethod
    def _edge_line(edge: Edge) -> str:
        return (
            f"- Edge `{edge.id}`: `{edge.source_id}` -> `{edge.target_id}` "
            f"kind `{edge.kind}`, layer `{edge.layer}`, confidence `{edge.confidence:.2f}`."
        )

    @staticmethod
    def _collect_spans(by_path: dict[str, list[str]], fact: Node | Edge) -> None:
        for span in fact.support:
            by_path[span.path].append(f"lines {span.start_line}-{span.end_line}")
