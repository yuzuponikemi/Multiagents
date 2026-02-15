from multiagents.agent.safety import SafetyModule


class TestSafetyModule:
    def setup_method(self):
        self.safety = SafetyModule()

    def test_safe_action(self):
        result = self.safety.check("set_laser", {"laser_power_mw": 50})
        assert result.is_safe is True
        assert result.violations == []
        assert result.reason == "OK"

    def test_parameter_out_of_range_high(self):
        result = self.safety.check("set_laser", {"laser_power_mw": 150})
        assert result.is_safe is False
        assert len(result.violations) == 1
        assert "out of safe range" in result.violations[0]

    def test_parameter_out_of_range_low(self):
        result = self.safety.check("set_flow", {"flow_rate_ul_min": 0})
        assert result.is_safe is False
        assert len(result.violations) == 1

    def test_parameter_at_boundary_min(self):
        result = self.safety.check("set_laser", {"laser_power_mw": 0})
        assert result.is_safe is True

    def test_parameter_at_boundary_max(self):
        result = self.safety.check("set_laser", {"laser_power_mw": 100})
        assert result.is_safe is True

    def test_prohibited_action(self):
        result = self.safety.check("disable_interlock", {})
        assert result.is_safe is False
        assert "Prohibited action" in result.violations[0]

    def test_multiple_violations(self):
        result = self.safety.check(
            "override_safety",
            {"laser_power_mw": 200, "pressure_psi": 50},
        )
        assert result.is_safe is False
        assert len(result.violations) == 3  # 1 prohibited + 2 range

    def test_unknown_parameter_ignored(self):
        result = self.safety.check("custom_action", {"unknown_param": 999})
        assert result.is_safe is True

    def test_all_parameter_ranges(self):
        # All within safe range
        result = self.safety.check("full_setup", {
            "laser_power_mw": 50,
            "flow_rate_ul_min": 50,
            "voltage_pmt": 500,
            "pressure_psi": 15,
        })
        assert result.is_safe is True
