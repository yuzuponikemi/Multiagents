from typer.testing import CliRunner

from multiagents.cli import app

runner = CliRunner()


class TestCLI:
    def test_agents_command(self, tmp_path, monkeypatch):
        """Test the agents listing command."""
        # Create test personas
        personas = tmp_path / "personas"
        personas.mkdir()
        (personas / "ghost.md").write_text(
            "# Ghost\n\n## Role\nSenior architect\n"
        )
        (personas / "coder.md").write_text(
            "# Coder\n\n## Role\nFast developer\n"
        )
        (personas / "_template.md").write_text("# Template\n")

        # Monkeypatch Settings at the config module level
        from multiagents.config import Settings

        original_init = Settings.__init__

        def patched_init(self, **kwargs):
            kwargs.setdefault("personas_dir", personas)
            original_init(self, **kwargs)

        monkeypatch.setattr(Settings, "__init__", patched_init)

        result = runner.invoke(app, ["agents"])
        assert result.exit_code == 0
        assert "ghost" in result.output
        assert "coder" in result.output
        # Template should be skipped
        assert "_template" not in result.output

    def test_review_file_not_found(self):
        """Test review command with nonexistent file."""
        result = runner.invoke(app, ["review", "/nonexistent/file.py", "--no-phoenix"])
        assert result.exit_code == 1

    def test_help(self):
        """Test help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "review" in result.output
        assert "triage" in result.output
        assert "meeting" in result.output
        assert "agents" in result.output
