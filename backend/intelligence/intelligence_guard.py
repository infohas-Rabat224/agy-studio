"""
Agy Studio v2.6 — Intelligence Guard
Intercepts proposals, commands, and plans that match rejected strategies or known regressions.
"""

from typing import Dict, Any, List, Optional
from .strategy_engine import StrategyEngine
from .regression_detector import RegressionDetector

class GuardCheckResult:
    def __init__(
        self,
        allowed: bool,
        violation: bool,
        warning: Optional[str] = None,
        rejected_pattern: Optional[str] = None,
        reason: Optional[str] = None,
        accepted_alternative: Optional[str] = None
    ):
        self.allowed = allowed
        self.violation = violation
        self.warning = warning
        self.rejected_pattern = rejected_pattern
        self.reason = reason
        self.accepted_alternative = accepted_alternative

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "violation": self.violation,
            "warning": self.warning,
            "rejected_pattern": self.rejected_pattern,
            "reason": self.reason,
            "accepted_alternative": self.accepted_alternative
        }

class IntelligenceGuard:
    """Evaluates proposals against rejected strategies and unresolved regressions."""

    def __init__(self, strategy_engine: StrategyEngine, regression_detector: RegressionDetector):
        self.strategy_engine = strategy_engine
        self.regression_detector = regression_detector

    def check_proposal(self, proposal: str) -> GuardCheckResult:
        clean = (proposal or "").strip().lower()

        # 1. Check against rejected strategies
        rejected_strategies = self.strategy_engine.list_strategies(status="REJECTED")
        for strat in rejected_strategies:
            strat_name = strat.name.lower()
            # Match either full name or significant keywords
            if strat_name in clean or (len(strat_name) > 5 and any(w in clean for w in strat_name.split() if len(w) > 4)):
                alt = None
                if strat.replacement_strategy_id:
                    alt_rec = self.strategy_engine.get_strategy_by_id(strat.replacement_strategy_id)
                    alt = alt_rec.name if alt_rec else strat.replacement_strategy_id
                return GuardCheckResult(
                    allowed=False,
                    violation=True,
                    warning=f"APPROCHE REJETÉE: '{strat.name}' a été formellement interdite.",
                    rejected_pattern=strat.name,
                    reason=strat.rejection_reason or "Approche rejetée lors d'un cycle précédent.",
                    accepted_alternative=alt
                )

        # 2. Check against active unresolved regressions
        unresolved = self.regression_detector.get_unresolved_regressions()
        for reg in unresolved:
            comp = reg.component.lower()
            if comp and comp in clean:
                return GuardCheckResult(
                    allowed=True,
                    violation=False,
                    warning=f"ATTENTION RÉGRESSION CONNUE: Le composant '{reg.component}' a régressé récemment. Exécuter '{reg.regression_test_cmd or 'pytest'}' après modification.",
                    rejected_pattern=None,
                    reason=reg.evidence
                )

        return GuardCheckResult(allowed=True, violation=False)
