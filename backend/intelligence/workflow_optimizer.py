"""
Agy Studio v2.6 — Workflow Optimizer & Project Intelligence
Synthesizes project architecture, runtime environments, and optimal execution pipelines.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

class ProjectIntelligenceProfile:
    def __init__(
        self,
        project_name: str,
        workspace_path: str,
        architecture_stack: List[str],
        successful_patterns: List[str],
        known_risks: List[str],
        preferred_workflow: List[str],
        environment_info: Dict[str, Any]
    ):
        self.project_name = project_name
        self.workspace_path = workspace_path
        self.architecture_stack = architecture_stack
        self.successful_patterns = successful_patterns
        self.known_risks = known_risks
        self.preferred_workflow = preferred_workflow
        self.environment_info = environment_info

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "workspace_path": self.workspace_path,
            "architecture_stack": self.architecture_stack,
            "successful_patterns": self.successful_patterns,
            "known_risks": self.known_risks,
            "preferred_workflow": self.preferred_workflow,
            "environment_info": self.environment_info
        }

class WorkflowOptimizer:
    """Infers project profiles and optimizes verification and execution pipelines."""

    @classmethod
    def probe_workspace_environment(cls, workspace_path: Optional[str] = None) -> Dict[str, Any]:
        ws = Path(workspace_path) if workspace_path else Path.cwd()
        info = {
            "os": sys.platform,
            "python_version": sys.version.split()[0],
            "runtime": "uv" if shutil.which("uv") or (ws / "runtime" / "uv.exe").exists() else "python",
            "workspace": str(ws),
            "ports_in_use": [8000, 8001],
            "native_bridge_available": (ws / "AgyStudioFolderPicker.exe").exists(),
            "has_pytest": (ws / "tests").exists(),
            "has_fastapi": True
        }
        return info

    @classmethod
    def generate_project_profile(
        cls,
        workspace_path: Optional[str] = None,
        active_strategies: Optional[List[str]] = None,
        regressions: Optional[List[str]] = None
    ) -> ProjectIntelligenceProfile:
        ws = Path(workspace_path) if workspace_path else Path.cwd()
        env = cls.probe_workspace_environment(str(ws))

        arch = ["FastAPI", "Windows Native Helper (C#)", "Astral UV Runtime", "SQLite Memory"]
        patterns = active_strategies or ["Async Native Helper for GUI", "Non-destructive Session Lineage", "Anti-Repetition Guard"]
        risks = regressions or ["Synchronous modal blockers in packaged runtime", "TTY-only agent invocations"]
        workflow = ["Real tests with pytest", "Evidence-based verification (exit code + artifact)", "Restart persistence verification"]

        return ProjectIntelligenceProfile(
            project_name=ws.name or "Agy Studio",
            workspace_path=str(ws),
            architecture_stack=arch,
            successful_patterns=patterns,
            known_risks=risks,
            preferred_workflow=workflow,
            environment_info=env
        )
