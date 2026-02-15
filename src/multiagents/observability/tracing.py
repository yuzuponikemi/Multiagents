from __future__ import annotations

from opentelemetry import trace

_initialized = False


def init_tracing(
    project_name: str = "multiagents-cytometer",
    endpoint: str = "http://localhost:6006",
) -> None:
    """Initialize Arize Phoenix tracing. Call once at startup."""
    global _initialized
    if _initialized:
        return

    from phoenix.otel import register

    register(
        project_name=project_name,
        endpoint=endpoint,
        auto_instrument=True,
    )
    _initialized = True


def get_tracer(name: str = "multiagents") -> trace.Tracer:
    """Get an OpenTelemetry tracer instance."""
    return trace.get_tracer(name)


def agent_span_attributes(
    agent_id: str,
    model_provider: str,
    task_type: str,
) -> dict[str, str]:
    """Return attribute dict for tagging agent spans."""
    return {
        "agent.id": agent_id,
        "agent.model_provider": model_provider,
        "agent.task_type": task_type,
    }
