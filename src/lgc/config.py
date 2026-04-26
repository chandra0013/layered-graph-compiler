import tomllib
from pathlib import Path

from pydantic import BaseModel


class ModelConfig(BaseModel):
    enabled: bool = False
    provider: str = "ollama"
    model: str = "qwen2.5-coder:7b"
    base_url: str = "http://localhost:11434"
    timeout_seconds: int = 30


class LgcConfig(BaseModel):
    models: ModelConfig = ModelConfig()


def load_config(root: Path) -> LgcConfig:
    path = Path(root) / "lgc.toml"
    if not path.exists():
        return LgcConfig()
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    return LgcConfig.model_validate(payload)
