from multiagents.agent.identity import IdentityModule


class TestIdentityModule:
    def test_load_persona_basic(self, temp_personas):
        module = IdentityModule(temp_personas)
        profile = module.load_persona("test_agent")

        assert profile.agent_id == "test_agent"
        assert profile.role == "Test role for unit testing"
        assert "Reliability first" in profile.values
        assert "Clean code" in profile.values
        assert "Prefers simplicity" in profile.biases
        assert profile.raci == {"Testing": "R", "Review": "C"}
        assert "test agent" in profile.background.lower()

    def test_load_persona_missing_file(self, tmp_path):
        module = IdentityModule(tmp_path)
        try:
            module.load_persona("nonexistent")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_build_system_prompt_basic(self, temp_personas):
        module = IdentityModule(temp_personas)
        profile = module.load_persona("test_agent")
        prompt = module.build_system_prompt(profile)

        assert "# Role: Test role for unit testing" in prompt
        assert "Reliability first" in prompt
        assert "Prefers simplicity" in prompt
        assert "Testing: R" in prompt

    def test_build_system_prompt_with_context(self, temp_personas):
        module = IdentityModule(temp_personas)
        profile = module.load_persona("test_agent")
        prompt = module.build_system_prompt(
            profile, context_sections=["# Arc42 Section\nSome content"]
        )

        assert "Architecture Context" in prompt
        assert "Arc42 Section" in prompt

    def test_build_system_prompt_with_memory(self, temp_personas):
        module = IdentityModule(temp_personas)
        profile = module.load_persona("test_agent")
        prompt = module.build_system_prompt(
            profile, skills_memory="- Always validate inputs before processing"
        )

        assert "Lessons Learned" in prompt
        assert "validate inputs" in prompt

    def test_parse_sections_static(self):
        raw = "# Title\n\n## Role\nTest role\n\n## Values\n- V1\n- V2\n"
        sections = IdentityModule._parse_sections(raw)
        assert "role" in sections
        assert "values" in sections
        assert "V1" in sections["values"]

    def test_parse_list_static(self):
        text = "- Item one\n- Item two\n* Item three\n"
        items = IdentityModule._parse_list(text)
        assert items == ["Item one", "Item two", "Item three"]

    def test_parse_raci_table_static(self):
        text = (
            "| Task Area | Level |\n"
            "|-----------|-------|\n"
            "| Design | R |\n"
            "| Testing | C |\n"
        )
        raci = IdentityModule._parse_raci_table(text)
        assert raci == {"Design": "R", "Testing": "C"}
