import pytest

from multiagents.tools.jira_tool import MockJiraClient
from multiagents.tools.obsidian_loader import ObsidianLoader


class TestMockJiraClient:
    def setup_method(self):
        self.client = MockJiraClient()

    def test_get_ticket(self):
        ticket = self.client.get_ticket("CYTO-101")
        assert ticket.ticket_id == "CYTO-101"
        assert "laser" in ticket.summary.lower()
        assert ticket.priority == "High"

    def test_get_ticket_not_found(self):
        with pytest.raises(KeyError):
            self.client.get_ticket("NONEXISTENT-999")

    def test_add_comment(self):
        self.client.add_comment("CYTO-101", "Test comment")
        ticket = self.client.get_ticket("CYTO-101")
        assert "Test comment" in ticket.comments

    def test_add_comment_not_found(self):
        with pytest.raises(KeyError):
            self.client.add_comment("NONEXISTENT-999", "comment")

    def test_list_tickets(self):
        tickets = self.client.list_tickets("CYTO")
        assert len(tickets) == 3

    def test_list_tickets_with_status(self):
        tickets = self.client.list_tickets("CYTO", status="Open")
        assert all(t.status == "Open" for t in tickets)

    def test_list_tickets_empty_project(self):
        tickets = self.client.list_tickets("NONEXIST")
        assert tickets == []


class TestObsidianLoader:
    def test_load_file(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "test.md").write_text("# Test Doc\nSome content here.")

        loader = ObsidianLoader(vault)
        doc = loader.load_file("test.md")

        assert doc.title == "Test Doc"
        assert "content here" in doc.content

    def test_load_file_not_found(self, tmp_path):
        loader = ObsidianLoader(tmp_path)
        with pytest.raises(FileNotFoundError):
            loader.load_file("nonexistent.md")

    def test_search_by_filename(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "laser_calibration.md").write_text("# Laser Calibration\nSteps...")
        (vault / "fluidics.md").write_text("# Fluidics\nPressure settings.")

        loader = ObsidianLoader(vault)
        results = loader.search("laser")

        assert len(results) == 1
        assert results[0].title == "Laser Calibration"

    def test_search_by_content(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "notes.md").write_text("# Notes\nThe PMT voltage should be 500V.")

        loader = ObsidianLoader(vault)
        results = loader.search("PMT")

        assert len(results) == 1

    def test_search_empty_vault(self, tmp_path):
        loader = ObsidianLoader(tmp_path / "nonexistent")
        results = loader.search("anything")
        assert results == []

    def test_list_files(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "a.md").write_text("A")
        (vault / "b.md").write_text("B")
        sub = vault / "sub"
        sub.mkdir()
        (sub / "c.md").write_text("C")

        loader = ObsidianLoader(vault)
        files = loader.list_files()

        assert len(files) == 3

    def test_list_files_skips_hidden(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "visible.md").write_text("V")
        hidden = vault / ".obsidian"
        hidden.mkdir()
        (hidden / "config.md").write_text("H")

        loader = ObsidianLoader(vault)
        files = loader.list_files()

        assert len(files) == 1
        assert files[0].name == "visible.md"

    def test_title_fallback(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "no_header.md").write_text("Just some text without a header.")

        loader = ObsidianLoader(vault)
        doc = loader.load_file("no_header.md")

        assert doc.title == "no_header"
