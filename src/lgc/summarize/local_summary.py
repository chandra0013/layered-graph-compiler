from lgc.domain.schemas import Node
from lgc.models.base import ModelUnavailableError, SummaryModel


class LocalSummaryService:
    def __init__(self, model: SummaryModel | None, enabled: bool = False) -> None:
        self.model = model
        self.enabled = enabled

    def enrich_nodes(self, nodes: list[Node]) -> list[Node]:
        if not self.enabled or self.model is None:
            return nodes

        enriched: list[Node] = []
        for node in nodes:
            if not node.support_node_ids:
                enriched.append(node)
                continue
            try:
                summary = self.model.summarize(_prompt_for(node))
            except ModelUnavailableError:
                return nodes
            if not summary:
                enriched.append(node)
                continue
            metadata = {**node.metadata, "summary_text": summary}
            enriched.append(node.model_copy(update={"metadata": metadata}))
        return enriched


def _prompt_for(node: Node) -> str:
    return (
        "Summarize only the supported graph node below. Do not invent facts.\n"
        f"id: {node.id}\n"
        f"label: {node.label}\n"
        f"metadata: {node.metadata}\n"
        f"support_node_ids: {node.support_node_ids}\n"
    )
