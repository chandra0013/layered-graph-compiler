import re
from pathlib import Path

from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Edge, EvidenceSpan, Node


RATIONALE_MARKERS = ("TODO:", "NOTE:", "WHY:", "IMPORTANT:", "HACK:", "FIXME:", "DECISION:", "ADR:")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
PLAIN_URL_RE = re.compile(r"(?<!\()https?://[^\s)]+")


def extract_text_document(path: Path, logical_path: str | None = None) -> tuple[list[Node], list[Edge]]:
    text = path.read_text(encoding="utf-8")
    extractor = TextDocumentExtractor(path, text, logical_path=logical_path)
    extractor.extract()
    return extractor.nodes, extractor.edges


class TextDocumentExtractor:
    def __init__(self, path: Path, text: str, logical_path: str | None = None) -> None:
        self.path = path
        self.path_key = logical_path or path.as_posix()
        self.lines = text.splitlines()
        self.nodes: list[Node] = []
        self.edges: list[Edge] = []
        self._node_ids: set[str] = set()
        self._edge_ids: set[str] = set()
        self.document_id = f"doc:document:{self.path_key}"

    def extract(self) -> None:
        self._add_node(
            self.document_id,
            self.path.stem,
            self._span(1, max(1, len(self.lines))),
            {"kind": "document", "path": self.path_key},
        )
        current_heading_id = self.document_id
        paragraph_lines: list[tuple[int, str]] = []

        for line_number, line in enumerate(self.lines, start=1):
            heading = self._heading_text(line, line_number)
            if heading:
                self._flush_paragraph(paragraph_lines, current_heading_id)
                paragraph_lines = []
                heading_id = f"doc:heading:{self.path_key}:{line_number}"
                self._add_node(heading_id, heading, self._span(line_number, line_number), {"kind": "heading", "path": self.path_key})
                self._add_edge(self.document_id, heading_id, "CONTAINS", self._span(line_number, line_number))
                current_heading_id = heading_id
                continue

            if line.strip():
                paragraph_lines.append((line_number, line))
            else:
                self._flush_paragraph(paragraph_lines, current_heading_id)
                paragraph_lines = []

        self._flush_paragraph(paragraph_lines, current_heading_id)

    def _flush_paragraph(self, lines: list[tuple[int, str]], parent_id: str) -> None:
        if not lines:
            return
        start_line = lines[0][0]
        end_line = lines[-1][0]
        text = " ".join(line.strip() for _line_number, line in lines)
        span = self._span(start_line, end_line)
        marker = _rationale_marker(text)
        kind = "rationale" if marker else "paragraph"
        node_id = f"doc:{kind}:{self.path_key}:{start_line}"
        self._add_node(
            node_id,
            text[:80],
            span,
            {"kind": kind, "path": self.path_key, "text": text, "marker": marker},
        )
        self._add_edge(parent_id, node_id, "CONTAINS", span)
        if marker:
            self._add_edge(node_id, parent_id, "RATIONALE_FOR", span)
        self._extract_links(text, node_id, span)

    def _extract_links(self, text: str, paragraph_id: str, span: EvidenceSpan) -> None:
        links = [(match.group(1), match.group(2)) for match in MARKDOWN_LINK_RE.finditer(text)]
        links.extend((match.group(0), match.group(0)) for match in PLAIN_URL_RE.finditer(text))
        for label, url in links:
            node_id = f"doc:link:{self.path_key}:{url}"
            self._add_node(node_id, label, span, {"kind": "link", "path": self.path_key, "url": url})
            self._add_edge(paragraph_id, node_id, "REFERENCES", span)

    def _heading_text(self, line: str, line_number: int) -> str | None:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
        if line_number < len(self.lines) and _is_rst_underline(self.lines[line_number], "="):
            return stripped or None
        if line_number < len(self.lines) and _is_rst_underline(self.lines[line_number], "-"):
            return stripped or None
        return None

    def _add_node(self, node_id: str, label: str, span: EvidenceSpan, metadata: dict[str, object]) -> None:
        if node_id in self._node_ids:
            return
        self._node_ids.add(node_id)
        self.nodes.append(
            Node(
                id=node_id,
                label=label,
                layer=Layer.L0,
                truth=TruthLabel.EXTRACTED,
                confidence=1.0,
                support=[span],
                metadata=metadata,
            )
        )

    def _add_edge(self, source_id: str, target_id: str, kind: str, span: EvidenceSpan) -> None:
        edge_id = f"doc:edge:{kind}:{source_id}:{target_id}:{span.start_line}"
        if edge_id in self._edge_ids:
            return
        self._edge_ids.add(edge_id)
        self.edges.append(
            Edge(
                id=edge_id,
                source_id=source_id,
                target_id=target_id,
                kind=kind,
                layer=Layer.L0,
                truth=TruthLabel.EXTRACTED,
                confidence=1.0,
                support=[span],
                metadata={"path": self.path_key},
            )
        )

    def _span(self, start_line: int, end_line: int) -> EvidenceSpan:
        return EvidenceSpan(
            path=self.path_key,
            start_line=start_line,
            end_line=end_line,
            snippet="\n".join(self.lines[start_line - 1 : end_line]),
        )


def _rationale_marker(text: str) -> str | None:
    upper = text.upper()
    for marker in RATIONALE_MARKERS:
        if marker in upper:
            return marker.rstrip(":")
    return None


def _is_rst_underline(line: str, char: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and set(stripped) == {char}
