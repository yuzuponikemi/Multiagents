from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract provider for swappable LLM backends."""

    @abstractmethod
    def get_chat_model(self) -> BaseChatModel:
        ...

    @abstractmethod
    def name(self) -> str:
        ...


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str, temperature: float = 0) -> None:
        self._base_url = base_url
        self._model = model
        self._temperature = temperature

    def get_chat_model(self) -> BaseChatModel:
        return ChatOllama(
            base_url=self._base_url,
            model=self._model,
            temperature=self._temperature,
        )

    def name(self) -> str:
        return f"ollama:{self._model}"


class StructuredCaller:
    """Wraps an LLM with Pydantic structured output + retry loop."""

    def __init__(self, provider: LLMProvider, max_retries: int = 2) -> None:
        self._provider = provider
        self._max_retries = max_retries

    def invoke(
        self,
        messages: list[BaseMessage | tuple[str, str]],
        output_schema: type[T],
    ) -> T:
        """
        Call LLM with structured output enforcement.
        On validation failure, feed error back and retry up to max_retries.
        """
        model = self._provider.get_chat_model()
        structured = model.with_structured_output(output_schema)

        # Normalize tuples to message objects
        normalized = self._normalize_messages(messages)

        last_error: Exception | None = None
        for _attempt in range(self._max_retries + 1):
            try:
                result = structured.invoke(normalized)
                return result
            except Exception as e:
                last_error = e
                normalized.append(
                    HumanMessage(
                        content=f"Previous attempt failed with: {e}\n"
                        "Please fix the output to match the required schema."
                    )
                )

        raise last_error  # type: ignore[misc]

    @staticmethod
    def _normalize_messages(
        messages: list[BaseMessage | tuple[str, str]],
    ) -> list[BaseMessage]:
        """Convert (role, content) tuples to LangChain message objects."""
        result: list[BaseMessage] = []
        for msg in messages:
            if isinstance(msg, BaseMessage):
                result.append(msg)
            elif isinstance(msg, tuple) and len(msg) == 2:
                role, content = msg
                if role == "system":
                    result.append(SystemMessage(content=content))
                else:
                    result.append(HumanMessage(content=content))
            else:
                raise ValueError(f"Unsupported message format: {msg}")
        return result
