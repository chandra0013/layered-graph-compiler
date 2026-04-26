from pathlib import Path


TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}


ROUTES_BY_EXTENSION = {
    ".py": "python_ast",
    ".md": "text_docs",
    ".rst": "text_docs",
    ".txt": "text_docs",
    ".json": "json",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
}


def detect_extension(path: Path) -> str:
    return path.suffix.lower()


def detect_file_type(path: Path) -> str:
    extension = detect_extension(path)
    if extension in TEXT_EXTENSIONS:
        return "text"

    sample = path.read_bytes()[:2048]
    if b"\0" in sample:
        return "binary"
    return "text"


def parser_route_for(path: Path) -> str:
    extension = detect_extension(path)
    if extension in ROUTES_BY_EXTENSION:
        return ROUTES_BY_EXTENSION[extension]
    if detect_file_type(path) == "text":
        return "text"
    return "binary_skip"
