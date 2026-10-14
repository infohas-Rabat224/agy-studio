import os
from typing import Dict, Any, Tuple, List, Optional
from .base import (
    BaseAgentAdapter, CapabilityStatus, ExecutionProfile, ExecutionMode,
    safe_run_process, ProviderDiagnostic
)

class CodexAdapter(BaseAgentAdapter):
    id = "codex"
    name = "OpenAI Codex CLI"
    command = "codex"
    provider = "openai"
    default_roles = ["CODER", "TESTER"]

    def check_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        # Run doctor to check local proxy vs direct API
        code, stdout, stderr, _, _ = safe_run_process([exe_path, "doctor"], timeout=6)
        
        out_lower = (stdout + " " + stderr).lower()
        has_nexus_proxy = "http://127.0.0.1:8787" in out_lower or "nexus" in out_lower
        nexus_offline = (
            "connect failed" in out_lower or
            "failed to connect" in out_lower or
            "unreachable" in out_lower or
            "connection refused" in out_lower
        )
        
        has_openai_env = bool(os.environ.get("OPENAI_API_KEY"))
        
        dependencies = {}
        if has_nexus_proxy or nexus_offline:
            dependencies["nexus_proxy"] = "UNAVAILABLE" if nexus_offline else "AVAILABLE"

        if has_openai_env and not nexus_offline:
            return "READY", {
                "auth_check": "CONFIGURED",
                "mode": "direct_openai",
                "dependencies": dependencies
            }
        elif nexus_offline:
            return "AUTH_REQUIRED", {
                "auth_check": "FAIL",
                "mode": "nexus_proxy",
                "error": "Local Nexus proxy at http://127.0.0.1:8787/v1 is offline",
                "dependencies": dependencies
            }
        return "AVAILABLE", {
            "auth_check": "NEEDS_CONFIG",
            "dependencies": dependencies
        }

    def probe_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return self.check_auth(exe_path)

    def get_execution_profile(self) -> ExecutionProfile:
        return ExecutionProfile(
            mode=ExecutionMode.NON_INTERACTIVE,
            command=[self.command, "exec"],
            arguments_template=["--skip-git-repo-check", "--ephemeral", "--dangerously-bypass-approvals-and-sandbox", "{prompt}"],
            stdin_mode="DEVNULL",
            timeout_seconds=60
        )

    def get_test_invocation(self, exe_path: str, prompt: str, provider_id: Optional[str] = None) -> List[str]:
        return [
            exe_path, "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--dangerously-bypass-approvals-and-sandbox",
            prompt
        ]

    def get_capabilities(self, exe_path: str, operational: bool = False) -> Dict[str, str]:
        st = CapabilityStatus.VERIFIED.value if operational else CapabilityStatus.DETECTED.value
        return {
            "chat": st,
            "code": st,
            "coding": st,
            "file_read": st,
            "file_write": st,
            "shell": st,
            "git": st,
            "sandbox": CapabilityStatus.DETECTED.value,
            "cancellation": CapabilityStatus.VERIFIED.value,
            "streaming": CapabilityStatus.DETECTED.value,
            "browser": CapabilityStatus.UNKNOWN.value,
            "playwright": CapabilityStatus.UNKNOWN.value,
            "non_interactive": CapabilityStatus.VERIFIED.value
        }
