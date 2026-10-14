"""
Agy Studio v2.6 — Risk Engine
Evaluates regression risks, historical failures, and unverified areas prior to task execution.
"""

from typing import Dict, Any, List, Optional

class RiskAssessment:
    def __init__(
        self,
        risk_level: str,  # LOW, MEDIUM, HIGH, CRITICAL
        risk_factors: List[str],
        known_regressions: List[str],
        mitigation_steps: List[str],
        unverified_areas: List[str]
    ):
        self.risk_level = risk_level
        self.risk_factors = risk_factors
        self.known_regressions = known_regressions
        self.mitigation_steps = mitigation_steps
        self.unverified_areas = unverified_areas

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "known_regressions": self.known_regressions,
            "mitigation_steps": self.mitigation_steps,
            "unverified_areas": self.unverified_areas
        }

class RiskEngine:
    """Computes real risk levels based on historical data, regressions, and components."""

    @classmethod
    def assess_risk(
        cls,
        task: str,
        target_components: List[str],
        rejected_approaches: List[Dict[str, Any]],
        regressions: List[Dict[str, Any]],
        has_verified_tests: bool = True
    ) -> RiskAssessment:
        factors = []
        mitigations = []
        unverified = []
        reg_names = []

        lower_task = (task or "").lower()

        # Check for components touching past regressions
        for reg in regressions:
            comp = reg.get("component", "").lower()
            feat = reg.get("feature_name", "").lower()
            if comp and (any(comp in c.lower() for c in target_components) or comp in lower_task or feat in lower_task):
                reg_names.append(f"{reg.get('feature_name', comp)} (broken previously)")
                factors.append(f"Subsystem '{comp}' has a recorded historical regression")
                mitigations.append(f"Run specific regression test: {reg.get('regression_test_cmd', 'pytest')}")

        # Check for rejected approaches matching task
        for rej in rejected_approaches:
            pattern = rej.get("rejected_approach") or rej.get("title") or rej.get("content", "")
            if pattern and any(p.strip().lower() in lower_task for p in pattern.split() if len(p) > 4):
                factors.append(f"Task keywords closely match rejected approach: {pattern}")
                mitigations.append("Strictly enforce Anti-Repetition Guard and substitute accepted alternative")

        # Check critical system components
        critical_keywords = ["bridge", "hwnd", "auth", "token", "delete", "format", "session lineage"]
        for ck in critical_keywords:
            if ck in lower_task:
                factors.append(f"Modifies sensitive core architecture area: '{ck}'")
                mitigations.append("Verify non-destructive persistence and backward compatibility")

        if not has_verified_tests:
            unverified.append("No automated test suite found for target components")
            factors.append("Missing verified tests for affected code path")
            mitigations.append("Require real runtime execution test with exit code and evidence check")

        # Determine level
        if any("broken previously" in r for r in reg_names) or len(factors) >= 3:
            level = "HIGH"
        elif len(factors) >= 1:
            level = "MEDIUM"
        else:
            level = "LOW"

        return RiskAssessment(
            risk_level=level,
            risk_factors=factors,
            known_regressions=reg_names,
            mitigation_steps=mitigations,
            unverified_areas=unverified
        )
