"""
Agy Studio v2.6 — Planning Engine & Adaptive Preflight
Constructs the complete 12-section Adaptive Preflight and optimizes execution contexts without mutating user intent.
"""

from typing import Dict, Any, List, Optional
from .intent_analyzer import IntentAnalysisResult
from .risk_engine import RiskAssessment
from .strategy_engine import StrategyRecord
from .experience_retriever import ExperienceRecord

class AdaptivePreflightResult:
    def __init__(
        self,
        task: str,
        user_corrections: List[Dict[str, Any]],
        hard_constraints: List[str],
        rejected_approaches: List[Dict[str, Any]],
        accepted_approaches: List[Dict[str, Any]],
        verified_solutions: List[Dict[str, Any]],
        related_experiences: List[Dict[str, Any]],
        learned_patterns: List[Dict[str, Any]],
        strategy_recommendations: List[Dict[str, Any]],
        agent_performance: List[str],
        regression_risks: List[str],
        required_verification: List[str],
        unknown_areas: List[str],
        recommended_agent: str = "antigravity",
        risk_level: str = "LOW"
    ):
        self.task = task
        self.user_corrections = user_corrections
        self.hard_constraints = hard_constraints
        self.rejected_approaches = rejected_approaches
        self.accepted_approaches = accepted_approaches
        self.verified_solutions = verified_solutions
        self.related_experiences = related_experiences
        self.learned_patterns = learned_patterns
        self.strategy_recommendations = strategy_recommendations
        self.agent_performance = agent_performance
        self.regression_risks = regression_risks
        self.required_verification = required_verification
        self.unknown_areas = unknown_areas
        self.recommended_agent = recommended_agent
        self.risk_level = risk_level

    def to_markdown(self) -> str:
        lines = ["=== AGY STUDIO ADAPTIVE INTELLIGENCE PREFLIGHT ==="]

        # 1. USER CORRECTIONS
        lines.append("\n[USER CORRECTIONS]")
        if self.user_corrections:
            for c in self.user_corrections:
                lines.append(f"• CRITICAL: {c.get('content') or c.get('title')}")
        else:
            lines.append("• Aucune correction directe applicable.")

        # 2. HARD CONSTRAINTS
        lines.append("\n[HARD CONSTRAINTS]")
        if self.hard_constraints:
            for hc in self.hard_constraints:
                lines.append(f"• {hc}")
        else:
            lines.append("• Respecter l'intégrité du runtime et les tests automatisés.")

        # 3. REJECTED APPROACHES
        lines.append("\n[REJECTED APPROACHES]")
        if self.rejected_approaches:
            for ra in self.rejected_approaches:
                app = ra.get("rejected_approach") or ra.get("name") or ra.get("title") or ra.get("content")
                reason = ra.get("reason") or ra.get("rejection_reason") or "Rejeté par l'utilisateur ou par échec d'exécution"
                lines.append(f"• INTERDIT: {app} — Motif: {reason}")
        else:
            lines.append("• Aucun schéma interdit détecté pour ce contexte.")

        # 4. ACCEPTED APPROACHES
        lines.append("\n[ACCEPTED APPROACHES]")
        if self.accepted_approaches:
            for aa in self.accepted_approaches:
                alt = aa.get("accepted_alternative") or aa.get("name") or aa.get("title") or aa.get("content")
                lines.append(f"• RECOMMANDÉ: {alt}")
        else:
            lines.append("• Utiliser les patterns d'architecture standards.")

        # 5. VERIFIED SOLUTIONS
        lines.append("\n[VERIFIED SOLUTIONS]")
        if self.verified_solutions:
            for vs in self.verified_solutions:
                lines.append(f"• VALIDÉ: {vs.get('title') or vs.get('name')}")
        else:
            lines.append("• Nouvelle zone d'implémentation — à vérifier.")

        # 6. RELATED EXPERIENCES
        lines.append("\n[RELATED EXPERIENCES]")
        if self.related_experiences:
            for rx in self.related_experiences:
                lines.append(f"• Expérience ({rx.get('outcome')}): {rx.get('task')[:80]}")
        else:
            lines.append("• Aucune exécution antérieure identique.")

        # 7. LEARNED PATTERNS
        lines.append("\n[LEARNED PATTERNS]")
        if self.learned_patterns:
            for lp in self.learned_patterns:
                lines.append(f"• Pattern [{lp.get('status')}]: {lp.get('signature')} — {lp.get('description')}")
        else:
            lines.append("• Aucun pattern récurrent identifié.")

        # 8. STRATEGY RECOMMENDATIONS
        lines.append("\n[STRATEGY RECOMMENDATIONS]")
        if self.strategy_recommendations:
            for sr in self.strategy_recommendations:
                lines.append(f"• Stratégie: {sr.get('name')} (Confiance: {sr.get('confidence')}, Succès: {sr.get('success_count')})")
        else:
            lines.append("• Stratégie par défaut: Analyse, TDD, Exécution, Preuve.")

        # 9. AGENT PERFORMANCE
        lines.append("\n[AGENT PERFORMANCE]")
        if self.agent_performance:
            for ap in self.agent_performance:
                lines.append(f"{ap}")
        else:
            lines.append(f"• Agent sélectionné: {self.recommended_agent} (Profil opérationnel vérifié)")

        # 10. REGRESSION RISKS
        lines.append("\n[REGRESSION RISKS]")
        if self.regression_risks:
            for rr in self.regression_risks:
                lines.append(f"• RISQUE: {rr}")
        else:
            lines.append(f"• Niveau de risque: {self.risk_level} — Faible risque de régression.")

        # 11. REQUIRED VERIFICATION
        lines.append("\n[REQUIRED VERIFICATION]")
        if self.required_verification:
            for rv in self.required_verification:
                lines.append(f"• {rv}")
        else:
            lines.append("• Code de sortie 0 + Vérification des artefacts produits.")

        # 12. UNKNOWN / UNVERIFIED AREAS
        lines.append("\n[UNKNOWN / UNVERIFIED AREAS]")
        if self.unknown_areas:
            for ua in self.unknown_areas:
                lines.append(f"• UNVERIFIED: {ua}")
        else:
            lines.append("• Tous les composants critiques sont répertoriés.")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "user_corrections": self.user_corrections,
            "hard_constraints": self.hard_constraints,
            "rejected_approaches": self.rejected_approaches,
            "accepted_approaches": self.accepted_approaches,
            "verified_solutions": self.verified_solutions,
            "related_experiences": self.related_experiences,
            "learned_patterns": self.learned_patterns,
            "strategy_recommendations": self.strategy_recommendations,
            "agent_performance": self.agent_performance,
            "regression_risks": self.regression_risks,
            "required_verification": self.required_verification,
            "unknown_areas": self.unknown_areas,
            "recommended_agent": self.recommended_agent,
            "risk_level": self.risk_level,
            "markdown": self.to_markdown()
        }

class PlanningEngine:
    """Builds preflights and optimizes execution prompts."""

    @classmethod
    def compile_preflight(
        cls,
        task: str,
        intent: IntentAnalysisResult,
        user_corrections: List[Dict[str, Any]],
        rejected_approaches: List[Dict[str, Any]],
        accepted_approaches: List[Dict[str, Any]],
        verified_solutions: List[Dict[str, Any]],
        experiences: List[ExperienceRecord],
        patterns: List[Dict[str, Any]],
        strategies: List[StrategyRecord],
        agent_explanations: List[str],
        risk: RiskAssessment,
        recommended_agent: str = "antigravity"
    ) -> AdaptivePreflightResult:
        req_verif = [
            "Exit code 0 required",
            "Exécution des tests automatisés pertinents (pytest)",
            "Vérification de présence et taille des artefacts"
        ]
        if "gui" in intent.target_components or "picker" in intent.target_components:
            req_verif.append("Validation de non-blocage de boucle UI (processus détaché)")

        exp_dicts = [e.to_dict() for e in experiences[:3]]
        strat_dicts = [s.to_dict() for s in strategies[:2]]

        return AdaptivePreflightResult(
            task=task,
            user_corrections=user_corrections,
            hard_constraints=intent.detected_constraints,
            rejected_approaches=rejected_approaches,
            accepted_approaches=accepted_approaches,
            verified_solutions=verified_solutions,
            related_experiences=exp_dicts,
            learned_patterns=patterns,
            strategy_recommendations=strat_dicts,
            agent_performance=agent_explanations,
            regression_risks=risk.risk_factors + risk.known_regressions,
            required_verification=req_verif,
            unknown_areas=risk.unverified_areas,
            recommended_agent=recommended_agent,
            risk_level=risk.risk_level
        )

    @classmethod
    def optimize_prompt(cls, raw_prompt: str, preflight_md: str) -> str:
        """Injects adaptive preflight context ahead of raw prompt without changing user intent."""
        return f"{preflight_md}\n\n[USER INSTRUCTION]\n{raw_prompt.strip()}"
