from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ObsidianDocument:
    """Represents a document loaded from an Obsidian vault."""

    path: Path
    title: str
    content: str


class ObsidianLoader:
    """Loads and searches Markdown files from an Obsidian vault directory."""

    def __init__(self, vault_path: Path) -> None:
        self._vault_path = vault_path

    @property
    def vault_path(self) -> Path:
        return self._vault_path

    def load_file(self, relative_path: str) -> ObsidianDocument:
        """Load a specific file from the vault."""
        path = self._vault_path / relative_path
        if not path.exists():
            raise FileNotFoundError(f"File not found in vault: {path}")
        content = path.read_text(encoding="utf-8")
        title = self._extract_title(content, path.stem)
        return ObsidianDocument(path=path, title=title, content=content)

    def search(self, query: str) -> list[ObsidianDocument]:
        """Search vault for documents matching query in filename or content."""
        if not self._vault_path.exists():
            return []

        query_lower = query.lower()
        results: list[ObsidianDocument] = []

        for md_file in self._vault_path.rglob("*.md"):
            # Skip hidden files and directories
            if any(part.startswith(".") for part in md_file.parts):
                continue

            content = md_file.read_text(encoding="utf-8")
            if query_lower in md_file.stem.lower() or query_lower in content.lower():
                title = self._extract_title(content, md_file.stem)
                results.append(
                    ObsidianDocument(path=md_file, title=title, content=content)
                )

        return results

    def list_files(self) -> list[Path]:
        """List all markdown files in the vault."""
        if not self._vault_path.exists():
            return []
        return sorted(
            p for p in self._vault_path.rglob("*.md")
            if not any(part.startswith(".") for part in p.parts)
        )

    @staticmethod
    def _extract_title(content: str, fallback: str) -> str:
        """Extract title from first H1 header, or use filename as fallback."""
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("##"):
                return stripped[2:].strip()
        return fallback
