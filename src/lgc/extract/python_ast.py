import ast
from pathlib import Path

from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Edge, EvidenceSpan, Node


def extract_python_ast(path: Path, logical_path: str | None = None) -> tuple[list[Node], list[Edge]]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    extractor = PythonAstExtractor(path, source, logical_path=logical_path)
    extractor.visit_module(tree)
    return extractor.nodes, extractor.edges


class PythonAstExtractor:
    def __init__(self, path: Path, source: str, logical_path: str | None = None) -> None:
        self.path = path
        self.source = source
        self.lines = source.splitlines() or [""]
        self.path_key = logical_path or path.as_posix()
        self.nodes: list[Node] = []
        self.edges: list[Edge] = []
        self._node_ids: set[str] = set()
        self._edge_ids: set[str] = set()
        self.module_id = f"py:module:{self.path_key}"

    def visit_module(self, tree: ast.Module) -> None:
        self._add_node(
            self.module_id,
            self.path.stem,
            span=self._span(1, len(self.lines)),
            metadata={
                "kind": "module",
                "path": self.path_key,
                "docstring": ast.get_docstring(tree),
            },
        )
        for statement in tree.body:
            self._visit_statement(statement, parent_id=self.module_id, class_name=None)

    def _visit_statement(
        self,
        statement: ast.stmt,
        parent_id: str,
        class_name: str | None,
    ) -> None:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            self._visit_import(statement, parent_id)
            return
        if isinstance(statement, ast.ClassDef):
            self._visit_class(statement, parent_id)
            return
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._visit_function(statement, parent_id, class_name)

    def _visit_import(self, statement: ast.Import | ast.ImportFrom, parent_id: str) -> None:
        modules = []
        if isinstance(statement, ast.Import):
            modules = [alias.name for alias in statement.names]
        else:
            base = statement.module or ""
            modules = [f"{base}.{alias.name}".strip(".") for alias in statement.names]

        for module in modules:
            node_id = f"py:import:{self.path_key}:{module}"
            self._add_node(
                node_id,
                module,
                span=self._span_for(statement),
                metadata={"kind": "import", "module": module, "path": self.path_key},
            )
            self._add_edge(parent_id, node_id, "IMPORTS", self._span_for(statement))

    def _visit_class(self, statement: ast.ClassDef, parent_id: str) -> None:
        node_id = f"py:class:{self.path_key}:{statement.name}"
        self._add_node(
            node_id,
            statement.name,
            span=self._span_for(statement),
            metadata={
                "kind": "class",
                "name": statement.name,
                "path": self.path_key,
                "docstring": ast.get_docstring(statement),
            },
        )
        self._add_edge(parent_id, node_id, "CONTAINS", self._span_for(statement))
        for child in statement.body:
            self._visit_statement(child, parent_id=node_id, class_name=statement.name)

    def _visit_function(
        self,
        statement: ast.FunctionDef | ast.AsyncFunctionDef,
        parent_id: str,
        class_name: str | None,
    ) -> None:
        kind = "method" if class_name else "function"
        qualified = f"{class_name}.{statement.name}" if class_name else statement.name
        node_id = f"py:{kind}:{self.path_key}:{qualified}"
        self._add_node(
            node_id,
            qualified,
            span=self._span_for(statement),
            metadata={
                "kind": kind,
                "name": statement.name,
                "qualified_name": qualified,
                "path": self.path_key,
                "docstring": ast.get_docstring(statement),
                "is_async": isinstance(statement, ast.AsyncFunctionDef),
            },
        )
        self._add_edge(parent_id, node_id, "CONTAINS", self._span_for(statement))
        self._visit_calls(statement, caller_id=node_id)

    def _visit_calls(
        self,
        statement: ast.FunctionDef | ast.AsyncFunctionDef,
        caller_id: str,
    ) -> None:
        for child in ast.walk(statement):
            if not isinstance(child, ast.Call):
                continue
            call_name = _simple_call_name(child.func)
            if not call_name:
                continue

            node_id = f"py:symbol:{call_name}"
            self._add_node(
                node_id,
                call_name,
                span=self._span_for(child),
                metadata={"kind": "external_symbol", "name": call_name},
            )
            self._add_edge(caller_id, node_id, "CALLS", self._span_for(child))

    def _add_node(
        self,
        node_id: str,
        label: str,
        span: EvidenceSpan,
        metadata: dict[str, object],
    ) -> None:
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

    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        kind: str,
        span: EvidenceSpan,
    ) -> None:
        edge_id = f"py:edge:{kind}:{source_id}:{target_id}:{span.start_line}"
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

    def _span_for(self, node: ast.AST) -> EvidenceSpan:
        return self._span(
            getattr(node, "lineno", 1),
            getattr(node, "end_lineno", getattr(node, "lineno", 1)),
        )

    def _span(self, start_line: int, end_line: int) -> EvidenceSpan:
        return EvidenceSpan(
            path=self.path_key,
            start_line=start_line,
            end_line=end_line,
            snippet="\n".join(self.lines[start_line - 1 : end_line]),
        )


def _simple_call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _simple_call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None
