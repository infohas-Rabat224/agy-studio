import os
from typing import Dict, Any, Tuple, List, Optional
from .base import (
    BaseAgentAdapter, CapabilityStatus, ExecutionProfile, ExecutionMode,
    safe_run_process
)

class GeminiAdapter(BaseAgentAdapter):
    id = "gemini"
    name = "Gemini CLI"
    command = "gemini"
    provider = "google"
    default_roles = ["RESEARCHER", "PLANNER"]

    def check_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        has_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
        if has_key:
            return "READY", {"auth_check": "CONFIGURED", "details": "Google/Gemini API key present"}
        return "AUTH_REQUIRED", {
            "auth_check": "NEEDS_KEY",
            "details": "Requires GEMINI_API_KEY or GOOGLE_API_KEY for generativeLanguage API"
        }

    def probe_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return self.check_auth(exe_path)

    def get_execution_profile(self) -> ExecutionProfile:
        return ExecutionProfile(
            mode=ExecutionMode.NON_INTERACTIVE,
            command=[self.command],
            arguments_template=["-p", "{prompt}"],
            stdin_mode="DEVNULL",
            timeout_seconds=60
        )

    def get_test_invocation(self, exe_path: str, prompt: str, provider_id: Optional[str] = None) -> List[str]:
        return [exe_path, "-p", prompt]

    def get_capabilities(self, exe_path: str, operational: bool = False) -> Dict[str, str]:
        st = CapabilityStatus.VERIFIED.value if operational else CapabilityStatus.DETECTED.value
        return {
            "chat": st,
            "code": st,
            "coding": st,
            "file_read": st,
            "file_write": st,
            "shell": st,
            "mcp": CapabilityStatus.DETECTED.value,
            "cancellation": CapabilityStatus.VERIFIED.value,
            "non_interactive": CapabilityStatus.VERIFIED.value
        }
