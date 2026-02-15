from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="multiagents",
    help="Multi-agent system for flow cytometer development.",
)


@app.command()
def review(
    file: Path = typer.Argument(..., help="Path to the code file to review"),
    phoenix: bool = typer.Option(True, help="Enable Phoenix tracing"),
    ollama_url: Optional[str] = typer.Option(None, help="Ollama base URL (for multi-PC)"),
) -> None:
    """Run a code review using the Architect Ghost agent."""
    from multiagents.config import Settings
    from multiagents.graphs.unit_review import run_unit_review

    settings = Settings()
    if phoenix:
        _init_phoenix(settings)
    provider = _make_provider(settings, ollama_url)

    if not file.exists():
        typer.echo(f"Error: File not found: {file}", err=True)
        raise typer.Exit(1)

    code = file.read_text(encoding="utf-8")
    typer.echo(f"Reviewing {file}...")

    result = run_unit_review(code, settings=settings, provider=provider)

    last_msg = result["messages"][-1].content if result["messages"] else "No response"
    typer.echo("\n--- Review Result ---")
    typer.echo(last_msg)


@app.command()
def triage(
    ticket: str = typer.Argument(..., help="JIRA ticket ID (e.g., CYTO-101)"),
    phoenix: bool = typer.Option(True, help="Enable Phoenix tracing"),
    ollama_url: Optional[str] = typer.Option(None, help="Ollama base URL"),
) -> None:
    """Triage a JIRA ticket using the Lab Analyst agent."""
    from multiagents.config import Settings
    from multiagents.graphs.triage import run_triage

    settings = Settings()
    if phoenix:
        _init_phoenix(settings)
    provider = _make_provider(settings, ollama_url)

    typer.echo(f"Triaging ticket {ticket}...")

    result = run_triage(ticket, settings=settings, provider=provider)

    last_msg = result["messages"][-1].content if result["messages"] else "No response"
    typer.echo("\n--- Triage Result ---")
    typer.echo(last_msg)


@app.command()
def meeting(
    topic: str = typer.Argument(..., help="Discussion topic"),
    phoenix: bool = typer.Option(True, help="Enable Phoenix tracing"),
    ollama_url: Optional[str] = typer.Option(None, help="Ollama base URL"),
) -> None:
    """Run a virtual lab meeting with all agents discussing a topic."""
    from multiagents.config import Settings
    from multiagents.graphs.lab_meeting import run_lab_meeting

    settings = Settings()
    if phoenix:
        _init_phoenix(settings)
    provider = _make_provider(settings, ollama_url)

    typer.echo(f"Starting lab meeting on: {topic}")
    typer.echo("Participants: Coder, Ghost (Architect), Analyst")
    typer.echo("---")

    result = run_lab_meeting(topic, settings=settings, provider=provider)

    typer.echo("\n--- Meeting Notes ---")
    for note in result.get("meeting_notes", []):
        typer.echo(note)

    typer.echo("\n--- Decision ---")
    typer.echo(result.get("decision", "No decision recorded"))

    typer.echo(f"\nRounds: {result.get('round_count', 0)}")


@app.command()
def agents() -> None:
    """List available agent personas."""
    from multiagents.config import Settings

    settings = Settings()
    personas_dir = settings.personas_dir

    if not personas_dir.exists():
        typer.echo("No personas directory found.")
        raise typer.Exit(1)

    typer.echo("Available agents:\n")
    for md_file in sorted(personas_dir.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        name = md_file.stem
        # Read first ## Role line
        role = ""
        for line in md_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("## Role"):
                continue
            if role == "" and line.strip() and not line.startswith("#"):
                role = line.strip()
                break
        typer.echo(f"  {name:20s} {role}")


def _init_phoenix(settings) -> None:
    """Initialize Phoenix tracing if enabled."""
    if settings.phoenix_enabled:
        try:
            from multiagents.observability.tracing import init_tracing

            init_tracing(
                project_name=settings.phoenix_project_name,
                endpoint=settings.phoenix_endpoint,
            )
        except Exception:
            pass  # Phoenix not available, continue without tracing


def _make_provider(settings, ollama_url: str | None = None):
    """Create an LLM provider with optional URL override."""
    from multiagents.agent.provider import OllamaProvider

    base_url = ollama_url or settings.ollama_base_url
    return OllamaProvider(base_url=base_url, model=settings.ollama_model)


if __name__ == "__main__":
    app()
