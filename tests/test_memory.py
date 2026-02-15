from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from multiagents.agent.memory import LongTermMemory, MemoryModule


class TestLongTermMemory:
    def test_read_empty(self, tmp_path):
        mem = LongTermMemory(tmp_path, "test_agent")
        assert mem.read() == ""

    def test_append_and_read(self, tmp_path):
        mem = LongTermMemory(tmp_path, "test_agent")
        mem.append_lesson("Always validate laser power before activation")
        content = mem.read()
        assert "Always validate laser power" in content
        assert content.startswith("- [")

    def test_append_multiple(self, tmp_path):
        mem = LongTermMemory(tmp_path, "test_agent")
        mem.append_lesson("Lesson 1")
        mem.append_lesson("Lesson 2")
        lines = [line for line in mem.read().splitlines() if line.strip()]
        assert len(lines) == 2

    def test_size_lines(self, tmp_path):
        mem = LongTermMemory(tmp_path, "test_agent")
        assert mem.size_lines() == 0
        mem.append_lesson("First lesson")
        assert mem.size_lines() == 1
        mem.append_lesson("Second lesson")
        assert mem.size_lines() == 2

    def test_creates_parent_dir(self, tmp_path):
        nested = tmp_path / "sub" / "dir"
        mem = LongTermMemory(nested, "test_agent")
        mem.append_lesson("test")
        assert mem.file_path.exists()


class TestMemoryModule:
    def test_should_compress_false(self, tmp_path):
        module = MemoryModule(tmp_path, "test", compression_threshold=20)
        assert module.should_compress(10) is False

    def test_should_compress_true(self, tmp_path):
        module = MemoryModule(tmp_path, "test", compression_threshold=20)
        assert module.should_compress(25) is True

    def test_compress_short_messages_unchanged(self, tmp_path, mock_llm):
        module = MemoryModule(tmp_path, "test")
        msgs = [HumanMessage(content="Hi"), AIMessage(content="Hello")]
        result = module.compress(msgs, mock_llm, keep_recent=5)
        assert result == msgs
        mock_llm.invoke.assert_not_called()

    def test_compress_long_messages(self, tmp_path, mock_llm):
        module = MemoryModule(tmp_path, "test")
        msgs = [HumanMessage(content=f"msg {i}") for i in range(10)]
        result = module.compress(msgs, mock_llm, keep_recent=3)

        # Should have 1 summary + 3 recent
        assert len(result) == 4
        assert isinstance(result[0], SystemMessage)
        assert "Previous context summary" in result[0].content
        assert result[1:] == msgs[-3:]
        mock_llm.invoke.assert_called_once()
