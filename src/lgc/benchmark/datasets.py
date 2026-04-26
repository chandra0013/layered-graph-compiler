from dataclasses import dataclass
from pathlib import Path

from lgc.benchmark.tokens import estimate_tokens
from lgc.ingest.manifest import walk_artifacts


@dataclass(frozen=True)
class BenchmarkDataset:
    root: Path
    file_count: int
    line_count: int
    raw_tokens: int


def load_local_repo(path: Path) -> BenchmarkDataset:
    root = Path(path).resolve()
    rows = [row for row in walk_artifacts(root) if row.parser_route != "binary_skip"]
    line_count = 0
    raw_tokens = 0
    for row in rows:
        try:
            text = (root / row.path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        line_count += len(text.splitlines())
        raw_tokens += estimate_tokens(text)
    return BenchmarkDataset(
        root=root,
        file_count=len(rows),
        line_count=line_count,
        raw_tokens=raw_tokens,
    )


def create_scaled_repo(root: Path, file_count: int, package: str = "pkg") -> Path:
    root = Path(root)
    package_dir = root / package
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    for index in range(file_count):
        (package_dir / f"module_{index}.py").write_text(
            "\n".join(
                [
                    f"def function_{index}():",
                    f"    return helper_{index}()",
                    "",
                    f"def helper_{index}():",
                    f"    return {index}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    return root
