from lgc.agents.base import ValidationContext, ValidationReport, Validator


class ParserAgent(Validator):
    name = "parser"

    def validate(self, context: ValidationContext) -> ValidationReport:
        errors: list[str] = []
        node_ids = [node.id for node in context.nodes_l0]
        edge_ids = [edge.id for edge in context.edges_l0]
        node_id_set = set(node_ids)

        _duplicates(node_ids, "duplicate node id", errors)
        _duplicates(edge_ids, "duplicate edge id", errors)
        for edge in context.edges_l0:
            if edge.source_id not in node_id_set:
                errors.append(f"edge references missing source: {edge.id}")
            if edge.target_id not in node_id_set:
                errors.append(f"edge references missing target: {edge.id}")

        return ValidationReport(
            name=self.name,
            passed=not errors,
            errors=errors,
            metrics={"nodes": len(node_ids), "edges": len(edge_ids)},
        )


def _duplicates(values: list[str], prefix: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            errors.append(f"{prefix}: {value}")
        seen.add(value)
