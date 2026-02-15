from multiagents.observability.tracing import agent_span_attributes, get_tracer


class TestTracing:
    def test_agent_span_attributes(self):
        attrs = agent_span_attributes(
            agent_id="test_agent",
            model_provider="ollama:qwen2.5",
            task_type="code_review",
        )
        assert attrs["agent.id"] == "test_agent"
        assert attrs["agent.model_provider"] == "ollama:qwen2.5"
        assert attrs["agent.task_type"] == "code_review"

    def test_get_tracer(self):
        tracer = get_tracer("test")
        assert tracer is not None
