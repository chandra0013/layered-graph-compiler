from enum import StrEnum


class TruthLabel(StrEnum):
    """How strongly a graph fact is grounded in source evidence."""

    EXTRACTED = "EXTRACTED"
    INFERRED = "INFERRED"
    AMBIGUOUS = "AMBIGUOUS"


class Layer(StrEnum):
    """Compiler abstraction layers."""

    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
