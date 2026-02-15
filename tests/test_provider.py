from unittest.mock import MagicMock

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from multiagents.agent.provider import (
    OllamaProvider,
    StructuredCaller,
)


class SimpleOutput(BaseModel):
    answer: str
    confidence: float


class TestOllamaProvider:
    def test_name(self):
        provider = OllamaProvider(base_url="http://localhost:11434", model="test-model")
        assert provider.name() == "ollama:test-model"

    def test_get_chat_model_returns_chat_ollama(self):
        provider = OllamaProvider(base_url="http://localhost:11434", model="test-model")
        model = provider.get_chat_model()
        assert model is not None


class TestStructuredCaller:
    def test_invoke_success_first_try(self):
        mock_provider = MagicMock()
        mock_model = MagicMock()
        mock_structured = MagicMock()
        expected = SimpleOutput(answer="test", confidence=0.9)
        mock_structured.invoke.return_value = expected
        mock_model.with_structured_output.return_value = mock_structured
        mock_provider.get_chat_model.return_value = mock_model

        caller = StructuredCaller(mock_provider, max_retries=2)
        result = caller.invoke(
            [("system", "You are a test agent")],
            SimpleOutput,
        )

        assert result == expected
        assert mock_structured.invoke.call_count == 1

    def test_invoke_retries_on_failure(self):
        mock_provider = MagicMock()
        mock_model = MagicMock()
        mock_structured = MagicMock()
        expected = SimpleOutput(answer="fixed", confidence=0.8)
        mock_structured.invoke.side_effect = [
            ValueError("bad schema"),
            expected,
        ]
        mock_model.with_structured_output.return_value = mock_structured
        mock_provider.get_chat_model.return_value = mock_model

        caller = StructuredCaller(mock_provider, max_retries=2)
        result = caller.invoke(
            [("system", "You are a test agent")],
            SimpleOutput,
        )

        assert result == expected
        assert mock_structured.invoke.call_count == 2

    def test_invoke_raises_after_max_retries(self):
        mock_provider = MagicMock()
        mock_model = MagicMock()
        mock_structured = MagicMock()
        mock_structured.invoke.side_effect = ValueError("persistent error")
        mock_model.with_structured_output.return_value = mock_structured
        mock_provider.get_chat_model.return_value = mock_model

        caller = StructuredCaller(mock_provider, max_retries=1)
        with pytest.raises(ValueError, match="persistent error"):
            caller.invoke([("system", "test")], SimpleOutput)

        # 1 initial + 1 retry = 2 total
        assert mock_structured.invoke.call_count == 2

    def test_normalize_messages_tuples(self):
        messages = [("system", "sys msg"), ("user", "user msg")]
        result = StructuredCaller._normalize_messages(messages)

        assert len(result) == 2
        assert isinstance(result[0], SystemMessage)
        assert isinstance(result[1], HumanMessage)
        assert result[0].content == "sys msg"

    def test_normalize_messages_mixed(self):
        messages = [
            SystemMessage(content="sys"),
            ("user", "user msg"),
        ]
        result = StructuredCaller._normalize_messages(messages)

        assert len(result) == 2
        assert isinstance(result[0], SystemMessage)
        assert isinstance(result[1], HumanMessage)
