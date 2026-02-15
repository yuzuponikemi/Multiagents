from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from multiagents.agent.context import ContextModule
from multiagents.agent.identity import IdentityModule, PersonaProfile
from multiagents.agent.memory import MemoryModule
from multiagents.agent.provider import LLMProvider, OllamaProvider, StructuredCaller
from multiagents.agent.safety import SafetyCheckResult, SafetyModule
from multiagents.config import Settings
from multiagents.observability.tracing import agent_span_attributes, get_tracer
from multiagents.state.graph_state import AgentState

T = TypeVar("T", bound=BaseModel)


class BaseAgent:
    """
    Composable agent with identity, memory, context, safety, and observability.
    Configure with different persona MD files to create specialized agents.
    """

    def __init__(
        self,
        agent_id: str,
        settings: Settings | None = None,
        provider: LLMProvider | None = None,
    ) -> None:
        self._settings = settings or Settings()
        self.agent_id = agent_id

        # Identity
        self._identity = IdentityModule(self._settings.personas_dir)
        self.persona: PersonaProfile = self._identity.load_persona(agent_id)

        # LLM Provider
        self._provider = provider or OllamaProvider(
            base_url=self._settings.ollama_base_url,
            model=self._settings.ollama_model,
        )
        self._caller = StructuredCaller(
            self._provider,
            max_retries=self._settings.max_structured_output_retries,
        )

        # Memory
        self._memory = MemoryModule(
            self._settings.memory_dir,
            agent_id,
            self._settings.memory_compression_threshold,
        )

        # Context
        self._context = ContextModule(self._settings.arc42_dir)
        self._arc42_sections = self._context.get_sections_for_role(self.persona.role)

        # Safety
        self._safety = SafetyModule()

        # Tracer
        self._tracer = get_tracer(f"agent.{agent_id}")

        # Build system prompt
        self._system_prompt = self._identity.build_system_prompt(
            self.persona,
            context_sections=self._arc42_sections,
            skills_memory=self._memory.long_term.read(),
        )

    @property
    def checkpointer(self):
        """LangGraph checkpointer for thread-level state persistence."""
        return self._memory.short_term.checkpointer

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    def reload_system_prompt(self) -> None:
        """Rebuild system prompt (e.g. after skills.md update)."""
        self._system_prompt = self._identity.build_system_prompt(
            self.persona,
            context_sections=self._arc42_sections,
            skills_memory=self._memory.long_term.read(),
        )

    def invoke(self, state: AgentState) -> AgentState:
        """Main entry point: process state and return updated state."""
        with self._tracer.start_as_current_span(
            f"agent.{self.agent_id}.invoke",
            attributes=agent_span_attributes(
                self.agent_id,
                self._provider.name(),
                state.get("current_task", "unknown"),
            ),
        ):
            messages = list(state["messages"])

            # Compress if needed
            if self._memory.should_compress(len(messages)):
                llm = self._provider.get_chat_model()
                messages = self._memory.compress(messages, llm)

            # Prepend system prompt
            full_messages = [("system", self._system_prompt)] + [
                (msg.type, msg.content) for msg in messages
            ]

            # Invoke LLM
            llm = self._provider.get_chat_model()
            response = llm.invoke(full_messages)

            return {**state, "messages": messages + [response]}

    def invoke_structured(
        self,
        state: AgentState,
        output_schema: type[T],
    ) -> T:
        """Invoke with structured output enforcement + retry."""
        with self._tracer.start_as_current_span(
            f"agent.{self.agent_id}.invoke_structured",
            attributes=agent_span_attributes(
                self.agent_id,
                self._provider.name(),
                state.get("current_task", "unknown"),
            ),
        ):
            messages = [("system", self._system_prompt)] + [
                (msg.type, msg.content) for msg in state["messages"]
            ]
            return self._caller.invoke(messages, output_schema)

    def check_safety(self, action: str, parameters: dict[str, float]) -> SafetyCheckResult:
        """Validate a physical action before execution."""
        return self._safety.check(action, parameters)

    def save_lesson(self, lesson: str) -> None:
        """Persist a lesson learned to long-term memory."""
        self._memory.long_term.append_lesson(lesson)

    def __repr__(self) -> str:
        return f"BaseAgent(id={self.agent_id!r}, role={self.persona.role!r})"
