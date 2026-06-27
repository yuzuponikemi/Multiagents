"""
ReAct-driven persona agent for Multiagents.

The default :class:`multiagents.agent.base.BaseAgent` does a single
LLM call per node. This subclass wraps test-smith's
:class:`test_smith.agents.react.ReActAgent` so that a persona can run a
tool-use loop (web search, code execution, fact-checking primitives,
etc.) inside one graph node while still keeping the persona / identity
/ memory / safety scaffolding from BaseAgent.

Layer rule: the ReAct loop itself lives in test-smith (the workspace
Agent Runtime). Multiagents is a domain framework on top — it
contributes the persona, the multi-agent debate orchestration, and the
domain-specific tools. Import direction is one-way:
``multiagents → test_smith``.

Lazy import: the ``test_smith`` dependency is optional. Install with
``uv sync --extra react`` (configured in pyproject.toml) before using
this class. If the import fails, a clear error tells the caller what
to do.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage, HumanMessage

from multiagents.agent.base import BaseAgent
from multiagents.config import Settings
from multiagents.state.graph_state import AgentState

if TYPE_CHECKING:  # pragma: no cover — typing only
    from test_smith.agents.react import Tool


def _import_react_agent() -> Any:
    """Import test_smith.agents.react lazily with a friendly error."""
    try:
        from test_smith.agents.react import ReActAgent

        return ReActAgent
    except ImportError as e:  # pragma: no cover — environment-dependent
        raise ImportError(
            "ReActPersonaAgent requires the `test-smith` package. "
            "Install it with: uv sync --extra react"
        ) from e


class ReActPersonaAgent(BaseAgent):
    """Persona agent whose `invoke` runs a ReAct tool-use loop.

    Drop-in replacement for :class:`BaseAgent` in a LangGraph node when
    the persona needs to plan over tools rather than just respond. The
    persona's system prompt (assembled from the MD file by
    :class:`IdentityModule`) is injected into the ReAct agent as
    ``extra_system_context`` so the persona's role / values / RACI are
    in scope while the agent loops.

    Args:
        agent_id: Persona identifier (matches ``personas/<id>.md``).
        tools: List of ``test_smith.agents.react.Tool`` instances the
            agent can call. Must include at least one terminal tool
            (``FinalAnswerTool`` or a domain-specific submit tool).
        settings: Optional Multiagents Settings.
        provider: Optional LLM provider override.
        max_iterations: ReAct loop cap.
        temperature: LLM temperature passed to the underlying chat model.
        verbose: Stream the ReAct trace to stdout.

    The latest ``HumanMessage`` in ``state["messages"]`` is fed to the
    ReAct loop as the question. The agent's final answer is appended as
    an ``AIMessage``. If the loop exits without a final answer (stuck or
    max-iterations), a stub ``AIMessage`` carries the failure reason so
    downstream nodes can route accordingly.
    """

    def __init__(
        self,
        agent_id: str,
        tools: list["Tool"],
        settings: Settings | None = None,
        provider: Any = None,
        max_iterations: int = 10,
        temperature: float = 0.3,
        verbose: bool = False,
    ) -> None:
        super().__init__(agent_id=agent_id, settings=settings, provider=provider)
        if not tools:
            raise ValueError(
                "ReActPersonaAgent requires at least one tool (e.g. "
                "FinalAnswerTool)."
            )
        self._tools = tools
        self._max_iterations = max_iterations
        self._temperature = temperature
        self._verbose = verbose
        self._react_agent_cls = _import_react_agent()

    def invoke(self, state: AgentState) -> AgentState:
        with self._tracer.start_as_current_span(
            f"agent.{self.agent_id}.invoke",
        ):
            messages = list(state["messages"])
            question = _extract_latest_human_message(messages) or (
                "Continue the task based on the conversation so far."
            )

            chat_model = self._provider.get_chat_model()
            # Some providers return a model with no ``temperature`` setter;
            # if our preferred temperature differs from the model's, try to
            # apply it via bind (LangChain's chat models support that),
            # falling back to whatever the provider configured.
            try:
                chat_model = chat_model.bind(temperature=self._temperature)
            except Exception:  # pragma: no cover — depends on model class
                pass

            agent = self._react_agent_cls(
                llm=chat_model,
                tools=self._tools,
                max_iterations=self._max_iterations,
                verbose=self._verbose,
                extra_system_context=self._system_prompt,
            )
            result = agent.run(question)

            if result.answer is not None:
                reply: Any = AIMessage(content=str(result.answer))
            else:
                reply = AIMessage(
                    content=(
                        f"[ReActPersonaAgent:{self.agent_id}] "
                        f"loop ended without a final answer "
                        f"(reason={result.stopped_reason!r}, "
                        f"iterations={len(result.steps)})."
                    )
                )

            return {**state, "messages": messages + [reply]}


def _extract_latest_human_message(messages: list[Any]) -> str | None:
    """Return the most recent HumanMessage's content, or None."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            content = msg.content
            return content if isinstance(content, str) else str(content)
    return None


__all__ = ["ReActPersonaAgent"]
