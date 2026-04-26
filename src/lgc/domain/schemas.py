from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lgc.domain.enums import Layer, TruthLabel


Metadata = dict[str, Any]


class EvidenceSpan(BaseModel):
    """A source location supporting a graph fact."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str | None = None
    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    start_col: int | None = Field(default=None, ge=0)
    end_col: int | None = Field(default=None, ge=0)
    snippet: str | None = None

    @model_validator(mode="after")
    def end_line_must_not_precede_start(self) -> "EvidenceSpan":
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self


class GraphFact(BaseModel):
    """Shared contract for nodes and edges."""

    model_config = ConfigDict(extra="forbid")

    id: str
    layer: Layer
    truth: TruthLabel
    confidence: float = Field(ge=0.0, le=1.0)
    support: list[EvidenceSpan] = Field(default_factory=list)
    support_node_ids: list[str] = Field(default_factory=list)
    metadata: Metadata = Field(default_factory=dict)

    @model_validator(mode="after")
    def extracted_facts_require_support(self) -> "GraphFact":
        if self.truth == TruthLabel.EXTRACTED and not self.support:
            raise ValueError("EXTRACTED facts must include at least one EvidenceSpan")
        return self


class Node(GraphFact):
    """A graph entity at one compiler layer."""

    label: str


class Edge(GraphFact):
    """A directed relationship between two graph nodes."""

    source_id: str
    target_id: str
    kind: str


class EvidencePacket(BaseModel):
    """A bounded set of grounded graph facts for answering a query."""

    model_config = ConfigDict(extra="forbid")

    query: str
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    token_budget: int | None = Field(default=None, gt=0)
    metadata: Metadata = Field(default_factory=dict)
