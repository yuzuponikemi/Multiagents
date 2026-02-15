from __future__ import annotations

from pathlib import Path

import yaml


class ContextModule:
    """Loads and injects relevant arc42 sections based on agent role."""

    def __init__(self, arc42_dir: Path) -> None:
        self._arc42_dir = arc42_dir
        self._section_map = self._load_section_map()

    def _load_section_map(self) -> dict[str, list[str]]:
        map_file = self._arc42_dir / "_section_map.yaml"
        if not map_file.exists():
            return {}
        return yaml.safe_load(map_file.read_text(encoding="utf-8")) or {}

    def get_sections_for_role(self, role: str) -> list[str]:
        """Return relevant arc42 section contents for a given role key."""
        filenames = self._section_map.get(role, [])
        sections: list[str] = []
        for fname in filenames:
            path = self._arc42_dir / fname
            if path.exists():
                sections.append(path.read_text(encoding="utf-8"))
        return sections
