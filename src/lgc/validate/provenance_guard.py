from lgc.domain.enums import TruthLabel
from lgc.domain.schemas import Edge, Node


class ProvenanceGuard:
    """Reject extracted facts that are not backed by source spans."""

    def validate(self, nodes: list[Node], edges: list[Edge]) -> None:
        for fact in [*nodes, *edges]:
            if fact.truth == TruthLabel.EXTRACTED and not fact.support:
                raise ValueError(f"EXTRACTED fact lacks provenance: {fact.id}")
