from lgc.agents.base import ValidationContext, ValidationReport, Validator
from lgc.domain.enums import TruthLabel
from lgc.domain.schemas import Edge, Node


class ProvenanceValidator(Validator):
    name = "provenance"

    def validate(self, context: ValidationContext) -> ValidationReport:
        errors: list[str] = []
        checked = 0
        for fact in [*context.nodes_l0, *context.edges_l0]:
            checked += 1
            errors.extend(_support_errors(fact, "edge" if isinstance(fact, Edge) else "node"))
        return ValidationReport(
            name=self.name,
            passed=not errors,
            errors=errors,
            metrics={"checked_objects": checked},
        )


def _support_errors(fact: Node | Edge, kind: str) -> list[str]:
    errors: list[str] = []
    if fact.truth != TruthLabel.EXTRACTED:
        return errors
    if not fact.support:
        return [f"{kind}:{fact.id} missing support"]
    for span in fact.support:
        if not span.path:
            errors.append(f"{kind}:{fact.id} span missing source_path")
        if span.start_line < 1:
            errors.append(f"{kind}:{fact.id} invalid line_start")
        if span.end_line < span.start_line:
            errors.append(f"{kind}:{fact.id} invalid line_end")
        if span.end_line - span.start_line > 10000:
            errors.append(f"{kind}:{fact.id} span too large")
    return errors
