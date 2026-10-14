"""
Agy Studio v2.6 — Task Classifier
Classifies tasks into domain categories and determines required capabilities.
"""

from typing import Dict, Any, List

class TaskClassifier:
    """Classifies user tasks into canonical task types and required capabilities."""

    TASK_CATEGORIES = {
        "GUI_AUTOMATION": ["picker", "folderpicker", "dialog", "window", "hwnd", "desktop", "native helper"],
        "DOCUMENT_GENERATION": ["docx", "pdf", "cahier", "fiche", "page", "table", "eval-fiche", "document"],
        "BACKEND_API": ["fastapi", "uvicorn", "endpoint", "route", "server", "middleware", "cors", "rest"],
        "TEST_VERIFICATION": ["pytest", "test", "verification", "gate", "forensic", "probe", "assert"],
        "SYSTEM_ADMIN": ["process", "bridge", "port", "kill", "taskkill", "runtime", "uv", "pip", "powershell"],
        "ORCHESTRATION": ["agent", "subagent", "route", "dispatch", "swarm", "model selection"],
    }

    REQUIRED_CAPS = {
        "GUI_AUTOMATION": ["desktop", "native_windows", "shell"],
        "DOCUMENT_GENERATION": ["python-docx", "filesystem", "pdf"],
        "BACKEND_API": ["fastapi", "asyncio", "python"],
        "TEST_VERIFICATION": ["pytest", "testing", "shell"],
        "SYSTEM_ADMIN": ["shell", "process_mgmt", "windows_api"],
        "ORCHESTRATION": ["chat", "orchestration", "multi_agent"],
        "GENERAL_CODING": ["chat", "code_generation", "python"]
    }

    @classmethod
    def classify(cls, task_text: str) -> Dict[str, Any]:
        lower = (task_text or "").lower()
        matched_scores: Dict[str, int] = {}

        for cat, keywords in cls.TASK_CATEGORIES.items():
            score = sum(1 for kw in keywords if kw in lower)
            if score > 0:
                matched_scores[cat] = score

        if not matched_scores:
            task_type = "GENERAL_CODING"
            confidence = 0.6
        else:
            best_cat = max(matched_scores.items(), key=lambda x: x[1])
            task_type = best_cat[0]
            confidence = min(0.95, 0.6 + (best_cat[1] * 0.15))

        caps = cls.REQUIRED_CAPS.get(task_type, ["chat", "python"])

        return {
            "task_type": task_type,
            "confidence": round(confidence, 2),
            "matched_keywords": matched_scores,
            "required_capabilities": caps
        }
