from __future__ import annotations

from pydantic import BaseModel, Field


class SafetyCheckResult(BaseModel):
    """Result of a physical safety validation check."""

    is_safe: bool
    reason: str = ""
    violations: list[str] = Field(default_factory=list)


class SafetyModule:
    """Validates physical tool calls against parameter ranges and prohibited actions."""

    PARAMETER_RANGES: dict[str, tuple[float, float]] = {
        "laser_power_mw": (0, 100),
        "flow_rate_ul_min": (1, 100),
        "voltage_pmt": (0, 1000),
        "pressure_psi": (0, 30),
    }

    PROHIBITED_ACTIONS: set[str] = {
        "disable_interlock",
        "override_safety",
        "bypass_calibration",
    }

    def check(self, action: str, parameters: dict[str, float]) -> SafetyCheckResult:
        """Validate an action and its parameters against safety constraints."""
        violations: list[str] = []

        if action in self.PROHIBITED_ACTIONS:
            violations.append(f"Prohibited action: {action}")

        for param, value in parameters.items():
            if param in self.PARAMETER_RANGES:
                lo, hi = self.PARAMETER_RANGES[param]
                if not (lo <= value <= hi):
                    violations.append(
                        f"{param}={value} out of safe range [{lo}, {hi}]"
                    )

        return SafetyCheckResult(
            is_safe=len(violations) == 0,
            violations=violations,
            reason="; ".join(violations) if violations else "OK",
        )
