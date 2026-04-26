from dataclasses import dataclass
from pathlib import Path

from lgc.benchmark.tokens import estimate_tokens
from lgc.ingest.manifest import walk_artifacts


@dataclass(frozen=True)
class BaselineResult:
    tokens: int
    chunk_count: int


def raw_context_baseline(root: Path) -> BaselineResult:
    """Return the total raw source tokens as if the entire repo is the context."""
    root = Path(root).resolve()
    total = 0
    file_count = 0
    for row in walk_artifacts(root):
        if row.parser_route == "binary_skip":
            continue
        try:
            total += estimate_tokens((root / row.path).read_text(encoding="utf-8"))
            file_count += 1
        except UnicodeDecodeError:
            continue
    return BaselineResult(tokens=total, chunk_count=file_count)


def keyword_chunk_baseline(root: Path, question: str, top_k: int = 5, chunk_lines: int = 40) -> BaselineResult:
    """Score fixed-size chunks by keyword overlap and return the top-k."""
    root = Path(root).resolve()
    terms = {part.lower() for part in question.split() if len(part) > 2}
    chunks: list[tuple[int, str]] = []
    for row in walk_artifacts(root):
        if row.parser_route == "binary_skip":
            continue
        try:
            lines = (root / row.path).read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for index in range(0, len(lines), chunk_lines):
            chunk = "\n".join(lines[index : index + chunk_lines])
            score = sum(1 for term in terms if term in chunk.lower() or term in row.path.lower())
            chunks.append((score, chunk))
    selected = [chunk for _score, chunk in sorted(chunks, key=lambda item: item[0], reverse=True)[:top_k]]
    return BaselineResult(tokens=sum(estimate_tokens(chunk) for chunk in selected), chunk_count=len(selected))


def naive_rag_baseline(root: Path, question: str, top_k: int = 5, chunk_lines: int = 40) -> BaselineResult:
    """Backward-compatible alias for keyword_chunk_baseline with top_k=5."""
    return keyword_chunk_baseline(root, question, top_k=top_k, chunk_lines=chunk_lines)


def file_level_keyword_baseline(root: Path, question: str, top_k: int = 3) -> BaselineResult:
    """Score entire files by keyword overlap and return the top-k files as context."""
    root = Path(root).resolve()
    terms = {part.lower() for part in question.split() if len(part) > 2}
    scored_files: list[tuple[int, str]] = []
    for row in walk_artifacts(root):
        if row.parser_route == "binary_skip":
            continue
        try:
            content = (root / row.path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        score = sum(1 for term in terms if term in content.lower() or term in row.path.lower())
        scored_files.append((score, content))
    selected = [content for _score, content in sorted(scored_files, key=lambda item: item[0], reverse=True)[:top_k]]
    return BaselineResult(tokens=sum(estimate_tokens(content) for content in selected), chunk_count=len(selected))
