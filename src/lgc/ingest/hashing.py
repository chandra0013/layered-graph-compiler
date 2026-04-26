from hashlib import sha256
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_id_for(relative_path: str, digest: str) -> str:
    return sha256(f"{relative_path}\0{digest}".encode("utf-8")).hexdigest()
