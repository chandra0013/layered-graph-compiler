from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SkipValidation

from lgc.domain.schemas import Edge, EvidencePacket, Node


class ValidationReport(BaseModel):
    name: str
    passed: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)


class ValidationContext(BaseModel):
    model_config = ConfigDict(revalidate_instances="never")

    nodes_l0: SkipValidation[list[Node]] = Field(default_factory=list)
    edges_l0: SkipValidation[list[Edge]] = Field(default_factory=list)
    nodes_l1: SkipValidation[list[Node]] = Field(default_factory=list)
    nodes_l2: SkipValidation[list[Node]] = Field(default_factory=list)
    nodes_l3: SkipValidation[list[Node]] = Field(default_factory=list)
    evidence_packet: EvidencePacket | None = None

    @property
    def all_nodes(self) -> list[Node]:
        return [*self.nodes_l0, *self.nodes_l1, *self.nodes_l2, *self.nodes_l3]


class Validator:
    name = "validator"

    def validate(self, context: ValidationContext) -> ValidationReport:
        raise NotImplementedError


def report_dict(reports: list[ValidationReport]) -> dict[str, Any]:
    return {report.name: report.model_dump(mode="json") for report in reports}
