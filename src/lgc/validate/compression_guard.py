from lgc.domain.enums import Layer
from lgc.domain.schemas import Node


class CompressionGuard:
    """Require compressed layers to cite the lower-layer nodes they summarize."""

    compressed_layers = {Layer.L1, Layer.L2, Layer.L3}

    def validate(self, nodes: list[Node]) -> None:
        for node in nodes:
            if node.layer in self.compressed_layers and not node.support_node_ids:
                raise ValueError(f"{node.layer} node lacks support_node_ids: {node.id}")
