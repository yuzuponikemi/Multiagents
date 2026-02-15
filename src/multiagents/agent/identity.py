from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PersonaProfile:
    agent_id: str
    role: str = ""
    values: list[str] = field(default_factory=list)
    biases: list[str] = field(default_factory=list)
    raci: dict[str, str] = field(default_factory=dict)
    background: str = ""
    raw_content: str = ""


class IdentityModule:
    """Loads persona MD files and builds system prompt fragments."""

    def __init__(self, personas_dir: Path) -> None:
        self._personas_dir = personas_dir

    def load_persona(self, agent_id: str) -> PersonaProfile:
        """Parse {agent_id}.md into a structured PersonaProfile."""
        path = self._personas_dir / f"{agent_id}.md"
        if not path.exists():
            raise FileNotFoundError(f"Persona file not found: {path}")

        raw = path.read_text(encoding="utf-8")
        sections = self._parse_sections(raw)

        return PersonaProfile(
            agent_id=agent_id,
            role=sections.get("role", "").strip(),
            values=self._parse_list(sections.get("values", "")),
            biases=self._parse_list(sections.get("biases", "")),
            raci=self._parse_raci_table(sections.get("raci", "")),
            background=sections.get("background", "").strip(),
            raw_content=raw,
        )

    def build_system_prompt(
        self,
        profile: PersonaProfile,
        context_sections: list[str] | None = None,
        skills_memory: str = "",
    ) -> str:
        """Assemble system prompt from persona + optional arc42 context + memory."""
        parts: list[str] = []

        # Identity block
        parts.append(f"# Role: {profile.role}")
        if profile.values:
            parts.append("\n## Core Values")
            for v in profile.values:
                parts.append(f"- {v}")
        if profile.biases:
            parts.append("\n## Thinking Biases")
            for b in profile.biases:
                parts.append(f"- {b}")
        if profile.raci:
            parts.append("\n## RACI Responsibilities")
            for area, level in profile.raci.items():
                parts.append(f"- {area}: {level}")
        if profile.background:
            parts.append(f"\n## Background\n{profile.background}")

        # Architecture context
        if context_sections:
            parts.append("\n---\n# Architecture Context")
            for section in context_sections:
                parts.append(section)

        # Long-term memory
        if skills_memory:
            parts.append("\n---\n# Lessons Learned")
            parts.append(skills_memory)

        return "\n".join(parts)

    @staticmethod
    def _parse_sections(raw: str) -> dict[str, str]:
        """Split MD content by ## headers into a dict."""
        sections: dict[str, str] = {}
        current_key: str | None = None
        current_lines: list[str] = []

        for line in raw.splitlines():
            header_match = re.match(r"^##\s+(.+)", line)
            if header_match:
                if current_key is not None:
                    sections[current_key] = "\n".join(current_lines)
                current_key = header_match.group(1).strip().lower()
                current_lines = []
            elif current_key is not None:
                current_lines.append(line)

        if current_key is not None:
            sections[current_key] = "\n".join(current_lines)

        return sections

    @staticmethod
    def _parse_list(text: str) -> list[str]:
        """Extract bullet items from markdown list text."""
        items = []
        for line in text.splitlines():
            match = re.match(r"^[-*]\s+(.+)", line.strip())
            if match:
                items.append(match.group(1).strip())
        return items

    @staticmethod
    def _parse_raci_table(text: str) -> dict[str, str]:
        """Parse a simple markdown table into {area: level} dict."""
        raci: dict[str, str] = {}
        for line in text.splitlines():
            # Skip header and separator lines
            if "|---" in line or "Task Area" in line:
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) == 2:
                raci[cells[0]] = cells[1]
        return raci
