from enum import StrEnum


class QueryIntent(StrEnum):
    OVERVIEW = "overview"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION_LOCALIZATION = "implementation-localization"
    FLOW_TRACING = "flow-tracing"
    RATIONALE = "rationale"
    UNKNOWN = "unknown"


_OVERVIEW_PHRASES = [
    "overview",
    "summary",
    "what is this",
    "explain project",
    "project description",
]

_ARCHITECTURE_PATTERNS = [
    "what exist",
    "what are the",
    "describe all",
    "what does the",
]

_ARCHITECTURE_PHRASES = [
    "architecture",
    "design",
    "layers",
    "subsystem",
    "hierarchy",
    "component",
    "structure",
    "mechanism",
]

_IMPLEMENTATION_WORDS = {
    "where",
    "implemented",
    "function",
    "class",
    "defined",
    "find",
    "locate",
    "contains",
}

_IMPLEMENTATION_PATTERNS = [
    "which file",
    "find the",
    "where is",
]

_FLOW_PHRASES = [
    "pipeline",
    "end-to-end",
    "full pipeline",
    "relationship",
    "between",
    "affect",
    "from scan",
    "from l0",
]

_FLOW_WORDS = {"calls", "call", "trace", "pipeline", "flow"}

_RATIONALE_WORDS = {"why", "rationale", "reason", "decision"}

# These words in _ARCHITECTURE_PHRASES can also be domain names,
# so they should only trigger ARCHITECTURE if the query does NOT
# contain implementation signals.
_DOMAIN_AMBIGUOUS = {"guard", "validation", "schema", "module"}


def classify_query(question: str) -> QueryIntent:
    text = question.lower()
    words = set(text.split())

    if any(phrase in text for phrase in _OVERVIEW_PHRASES):
        return QueryIntent.OVERVIEW

    has_impl_signal = _has_implementation_word(text, words)

    # Implementation patterns — "find the X", "where is X", "which file"
    if any(pattern in text for pattern in _IMPLEMENTATION_PATTERNS):
        return QueryIntent.IMPLEMENTATION_LOCALIZATION
    # Implementation words — but only if no flow/architecture phrase is dominant
    if has_impl_signal and not _has_flow_signal(text, words) and not _has_architecture_pattern(text):
        return QueryIntent.IMPLEMENTATION_LOCALIZATION

    # Flow tracing
    if _has_flow_signal(text, words):
        return QueryIntent.FLOW_TRACING

    # Architecture — patterns first (multi-word), then single-word phrases
    if _has_architecture_pattern(text):
        return QueryIntent.ARCHITECTURE
    if any(phrase in text for phrase in _ARCHITECTURE_PHRASES):
        return QueryIntent.ARCHITECTURE
    # Ambiguous domain words only trigger architecture if there's a "describe/explain/how" lead-in
    if words & _DOMAIN_AMBIGUOUS and _has_descriptive_lead(text):
        return QueryIntent.ARCHITECTURE

    if words & _RATIONALE_WORDS:
        return QueryIntent.RATIONALE

    return QueryIntent.UNKNOWN


def _has_implementation_word(text: str, words: set[str]) -> bool:
    for keyword in _IMPLEMENTATION_WORDS:
        if " " in keyword:
            if keyword in text:
                return True
        elif keyword in words:
            return True
    return False


def _has_flow_signal(text: str, words: set[str]) -> bool:
    if any(phrase in text for phrase in _FLOW_PHRASES):
        return True
    return bool(words & _FLOW_WORDS)


def _has_architecture_pattern(text: str) -> bool:
    return any(pattern in text for pattern in _ARCHITECTURE_PATTERNS)


def _has_descriptive_lead(text: str) -> bool:
    return any(lead in text for lead in [
        "describe the", "describe all", "explain", "how does the",
        "how are", "what does the", "what exist",
    ])
