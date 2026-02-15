# 9. Architecture Decisions

## ADR-001: Multi-Agent over Monolithic LLM
**Decision**: Use specialized agents with distinct personas instead of a single general-purpose LLM.
**Rationale**: Domain expertise (firmware, safety, architecture) requires different reasoning biases. Composition allows independent improvement of each capability.

## ADR-002: Local-First LLM with Cloud Fallback
**Decision**: Default to Ollama (local) with optional Gemini fallback.
**Rationale**: Instrument IP and patient data must not leave the local network by default. Cloud LLM used only for non-sensitive architectural reasoning with explicit approval.

## ADR-003: Obsidian as Single Source of Truth
**Decision**: All knowledge (architecture docs, personas, lessons) stored as Markdown in Obsidian-compatible format.
**Rationale**: Human-readable, version-controllable, and directly consumable as LLM context without transformation.

## ADR-004: Physical Safety Guardrails
**Decision**: All physical tool calls must pass through SafetyCheckNode before execution.
**Rationale**: Incorrect laser power or pressure settings can damage the instrument or samples. AI must never bypass safety validation.
