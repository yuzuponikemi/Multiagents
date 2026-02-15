from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Paths
    project_root: Path = _project_root()
    personas_dir: Path = _project_root() / "personas"
    arc42_dir: Path = _project_root() / "arc42"
    memory_dir: Path = _project_root() / "_memory"
    obsidian_vault_path: Path = _project_root() / "obsidian"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"

    # Phoenix
    phoenix_enabled: bool = True
    phoenix_endpoint: str = "http://localhost:6006"
    phoenix_project_name: str = "multiagents-cytometer"

    # Memory
    memory_compression_threshold: int = 20

    # Safety
    max_structured_output_retries: int = 2

    model_config = {"env_prefix": "MA_"}
