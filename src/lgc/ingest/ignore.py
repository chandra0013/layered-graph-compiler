from fnmatch import fnmatch
from pathlib import Path


DEFAULT_IGNORES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "lgc-out",
    "artifact_manifest.jsonl",
    "edges_l0.json",
    "evidence_packet.json",
    "graph_l0.json",
    "nodes_l0.json",
    "nodes_l1.json",
    "nodes_l2.json",
    "nodes_l3.json",
}


class LgcIgnore:
    def __init__(self, patterns: list[str] | None = None) -> None:
        self.patterns = patterns or []

    @classmethod
    def from_root(cls, root: Path) -> "LgcIgnore":
        ignore_file = root / ".lgcignore"
        if not ignore_file.exists():
            return cls()

        patterns = []
        for line in ignore_file.read_text(encoding="utf-8").splitlines():
            pattern = line.strip()
            if pattern and not pattern.startswith("#"):
                patterns.append(pattern)
        return cls(patterns)

    def is_ignored(self, relative_path: Path, is_dir: bool = False) -> bool:
        normalized = relative_path.as_posix()
        parts = set(relative_path.parts)
        if parts & DEFAULT_IGNORES:
            return True

        for pattern in self.patterns:
            if self._matches(pattern, normalized, relative_path.name, is_dir):
                return True
        return False

    @staticmethod
    def _matches(pattern: str, path: str, name: str, is_dir: bool) -> bool:
        directory_only = pattern.endswith("/")
        clean = pattern.rstrip("/")
        if directory_only and not is_dir and not path.startswith(f"{clean}/"):
            return False
        if fnmatch(path, clean) or fnmatch(name, clean):
            return True
        return path == clean or path.startswith(f"{clean}/")
