from multiagents.agent.context import ContextModule


class TestContextModule:
    def test_get_sections_for_known_role(self, temp_arc42):
        module = ContextModule(temp_arc42)
        sections = module.get_sections_for_role("test_role")

        assert len(sections) == 2
        assert "Introduction" in sections[0]
        assert "Building Blocks" in sections[1]

    def test_get_sections_for_unknown_role(self, temp_arc42):
        module = ContextModule(temp_arc42)
        sections = module.get_sections_for_role("nonexistent_role")

        assert sections == []

    def test_get_sections_for_partial_role(self, temp_arc42):
        module = ContextModule(temp_arc42)
        sections = module.get_sections_for_role("other_role")

        assert len(sections) == 1
        assert "Introduction" in sections[0]

    def test_missing_section_map(self, tmp_path):
        empty_dir = tmp_path / "empty_arc42"
        empty_dir.mkdir()
        module = ContextModule(empty_dir)
        sections = module.get_sections_for_role("any_role")

        assert sections == []

    def test_missing_referenced_file(self, tmp_path):
        arc42_dir = tmp_path / "arc42"
        arc42_dir.mkdir()
        (arc42_dir / "_section_map.yaml").write_text(
            "test_role:\n  - missing_file.md\n"
        )
        module = ContextModule(arc42_dir)
        sections = module.get_sections_for_role("test_role")

        assert sections == []
