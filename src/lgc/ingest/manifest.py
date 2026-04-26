import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from lgc.ingest.detect import detect_extension, parser_route_for
from lgc.ingest.hashing import artifact_id_for, sha256_file
from lgc.ingest.ignore import LgcIgnore


class ArtifactManifestRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    path: str
    sha256: str
    size_bytes: int = Field(ge=0)
    extension: str
    parser_route: str


def walk_artifacts(root: Path) -> list[ArtifactManifestRow]:
    root = root.resolve()
    ignore = LgcIgnore.from_root(root)
    rows: list[ArtifactManifestRow] = []

    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ignore.is_ignored(relative, is_dir=path.is_dir()):
            continue
        if not path.is_file():
            continue

        relative_posix = relative.as_posix()
        digest = sha256_file(path)
        rows.append(
            ArtifactManifestRow(
                artifact_id=artifact_id_for(relative_posix, digest),
                path=relative_posix,
                sha256=digest,
                size_bytes=path.stat().st_size,
                extension=detect_extension(path),
                parser_route=parser_route_for(path),
            )
        )

    return rows


def write_manifest(
    root: Path,
    output_path: Path | None = None,
) -> list[ArtifactManifestRow]:
    root = root.resolve()
    output_path = output_path or root / "artifact_manifest.jsonl"
    rows = walk_artifacts(root)

    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.model_dump(), sort_keys=True))
            handle.write("\n")

    return rows
