from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver


class ShortTermMemory:
    """Thin wrapper around LangGraph checkpointer for thread context."""

    def __init__(self) -> None:
        self._checkpointer = MemorySaver()

    @property
    def checkpointer(self) -> MemorySaver:
        return self._checkpointer


class LongTermMemory:
    """Per-agent skills/lessons file in _memory/ directory."""

    def __init__(self, memory_dir: Path, agent_id: str) -> None:
        self._file = memory_dir / f"{agent_id}_skills.md"

    @property
    def file_path(self) -> Path:
        return self._file

    def read(self) -> str:
        if self._file.exists():
            return self._file.read_text(encoding="utf-8")
        return ""

    def append_lesson(self, lesson: str) -> None:
        self._file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._file.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp}] {lesson}\n")

    def size_lines(self) -> int:
        if not self._file.exists():
            return 0
        return len(self._file.read_text(encoding="utf-8").splitlines())


class MemoryModule:
    """Combines short-term and long-term memory for an agent."""

    def __init__(
        self,
        memory_dir: Path,
        agent_id: str,
        compression_threshold: int = 20,
    ) -> None:
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(memory_dir, agent_id)
        self._threshold = compression_threshold

    def should_compress(self, message_count: int) -> bool:
        return message_count > self._threshold

    def compress(
        self,
        messages: list[BaseMessage],
        llm: BaseChatModel,
        keep_recent: int = 5,
    ) -> list[BaseMessage]:
        """Summarize older messages using the LLM, keep recent ones."""
        if len(messages) <= keep_recent:
            return messages

        old = messages[:-keep_recent]
        recent = messages[-keep_recent:]

        summary_response = llm.invoke(
            [SystemMessage(content="Summarize the following conversation concisely.")]
            + old
        )

        return [
            SystemMessage(content=f"Previous context summary: {summary_response.content}"),
            *recent,
        ]
