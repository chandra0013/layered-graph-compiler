from lgc.agents.base import ValidationContext, ValidationReport, Validator


class OntologyAgent(Validator):
    name = "ontology"

    def validate(self, context: ValidationContext) -> ValidationReport:
        warnings: list[str] = []
        for node in context.all_nodes:
            kind = node.metadata.get("kind")
            if not kind:
                warnings.append(f"node kind is empty: {node.id}")
            if not node.label:
                warnings.append(f"label is empty: {node.id}")
            if node.label != node.label.strip():
                warnings.append(f"label has leading/trailing whitespace: {node.id}")
            if len(node.label) > 200:
                warnings.append(f"label too long: {node.id}")
        for edge in context.edges_l0:
            if not edge.kind:
                warnings.append(f"edge kind is empty: {edge.id}")
        return ValidationReport(
            name=self.name,
            passed=True,
            warnings=warnings,
            metrics={"checked_nodes": len(context.all_nodes), "checked_edges": len(context.edges_l0)},
        )
