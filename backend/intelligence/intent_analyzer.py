"""
Agy Studio v2.6 — Intent Analyzer
Extracts primary goal, target components, action types, constraints, and corrections from prompts.
"""

import re
from typing import Dict, Any, List, Optional

class IntentAnalysisResult:
    def __init__(
        self,
        raw_prompt: str,
        primary_goal: str,
        target_components: List[str],
        action_type: str,
        detected_constraints: List[str],
        is_user_correction: bool = False,
        correction_details: Optional[Dict[str, str]] = None,
        confidence: float = 0.85
    ):
        self.raw_prompt = raw_prompt
        self.primary_goal = primary_goal
        self.target_components = target_components
        self.action_type = action_type
        self.detected_constraints = detected_constraints
        self.is_user_correction = is_user_correction
        self.correction_details = correction_details or {}
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_prompt": self.raw_prompt,
            "primary_goal": self.primary_goal,
            "target_components": self.target_components,
            "action_type": self.action_type,
            "detected_constraints": self.detected_constraints,
            "is_user_correction": self.is_user_correction,
            "correction_details": self.correction_details,
            "confidence": round(self.confidence, 2)
        }

class IntentAnalyzer:
    """Parses user prompts into structured intent components."""

    KNOWN_COMPONENTS = [
        "workspace picker", "folder picker", "picker", "folderpicker.exe",
        "session", "session manager", "memory", "sqlite", "fastapi", "uvicorn",
        "orchestrator", "agent", "bridge", "native bridge", "docx", "pdf",
        "playwright", "browser", "cahier de text", "eval-fiche", "matrix terminal",
        "command palette", "header", "preview", "artifacts", "uv", "runtime"
    ]

    CORRECTION_PATTERNS = [
        r"(?:ne jamais|never)\s+(?:utiliser|use|faire|do)\s+([^,.]+)",
        r"(?:n['’]utilise pas|don['’]t use|do not use)\s+([^,.]+)",
        r"(?:rejeter|reject|refuser|ban)\s+([^,.]+)",
        r"(?:utiliser plutôt|use instead|privilégier)\s+([^,.]+)",
        r"([^,.]+)\s+(?:est rejeté|est interdit|is rejected|is invalid)",
        r"(?:cette solution est fausse|wrong solution|incorrect approach)\s*[:.-]?\s*([^,.]*)"
    ]

    @classmethod
    def analyze(cls, prompt: str) -> IntentAnalysisResult:
        clean = (prompt or "").strip()
        lower = clean.lower()

        # 1. Action type detection
        action_type = "GENERAL_TASK"
        if any(w in lower for w in ["fix", "réparer", "corriger", "bug", "problème", "erreur"]):
            action_type = "FIX"
        elif any(w in lower for w in ["créer", "create", "build", "implémenter", "implement", "nouveau"]):
            action_type = "BUILD"
        elif any(w in lower for w in ["optimiser", "optimize", "refactor", "nettoyer", "clean"]):
            action_type = "OPTIMIZE"
        elif any(w in lower for w in ["tester", "test", "vérifier", "verify", "valider", "check"]):
            action_type = "VERIFY"
        elif any(w in lower for w in ["inspecter", "inspect", "chercher", "search", "analyser", "explore"]):
            action_type = "INSPECT"

        # 2. Extract target components
        found_components = []
        for comp in cls.KNOWN_COMPONENTS:
            if comp in lower and comp not in found_components:
                found_components.append(comp)

        # 3. Detect constraints
        constraints = []
        if "sans mock" in lower or "no mock" in lower:
            constraints.append("no_mocks")
        if "runtime réel" in lower or "real runtime" in lower:
            constraints.append("real_runtime_required")
        if "sans modification" in lower or "never modify directly" in lower:
            constraints.append("immutable_master")
        if "zero page blanche" in lower or "0 extra blank" in lower:
            constraints.append("zero_blank_pages")

        # 4. Detect user corrections
        is_correction = False
        correction_details = {}
        for pattern in cls.CORRECTION_PATTERNS:
            match = re.search(pattern, clean, re.IGNORECASE)
            if match:
                is_correction = True
                rejected = match.group(1).strip()
                correction_details["rejected_entity"] = rejected
                # Try finding alternative
                alt_match = re.search(r"(?:utiliser|use|utilise)\s+([A-Za-z0-9_.-]+)\s+(?:à la place|instead)", clean, re.IGNORECASE)
                if alt_match:
                    correction_details["accepted_alternative"] = alt_match.group(1).strip()
                break

        # 5. Extract primary goal
        first_line = clean.split("\n")[0].strip()
        goal = first_line[:120] if len(first_line) > 120 else first_line
        if not goal:
            goal = "Tâche non spécifiée"

        return IntentAnalysisResult(
            raw_prompt=clean,
            primary_goal=goal,
            target_components=found_components,
            action_type=action_type,
            detected_constraints=constraints,
            is_user_correction=is_correction,
            correction_details=correction_details,
            confidence=0.9 if found_components else 0.75
        )
