from lgc.agents.base import ValidationContext, ValidationReport, Validator


class CompressionValidator(Validator):
    name = "compression"

    def validate(self, context: ValidationContext) -> ValidationReport:
        errors: list[str] = []
        nodes = [*context.nodes_l1, *context.nodes_l2, *context.nodes_l3]
        for node in nodes:
            if not node.support_node_ids:
                errors.append(f"{node.id} missing support_node_ids")
        return ValidationReport(
            name=self.name,
            passed=not errors,
            errors=errors,
            metrics={"checked_nodes": len(nodes)},
        )
