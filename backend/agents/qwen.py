import os
from typing import Dict, Any, Tuple, List, Optional
from .base import (
    BaseAgentAdapter, CapabilityStatus, ExecutionProfile, ExecutionMode,
    check_conpty_support
)

class QwenAdapter(BaseAgentAdapter):
    id = "qwen"
    name = "Qwen Code CLI"
    command = "qwen"
    provider = "alibaba"
    default_roles = ["CODER", "REVIEWER"]

    def check_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        has_key = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("DASHSCOPE_API_KEY"))
        if has_key:
            return "READY", {
                "auth_check": "CONFIGURED",
                "details": "API Key detected in environment",
                "conpty_supported": check_conpty_support()
            }
        return "AVAILABLE", {
            "auth_check": "NEEDS_CONFIG",
            "details": "Requires OPENAI_API_KEY / DASHSCOPE_API_KEY or interactive TTY session",
            "conpty_supported": check_conpty_support()
        }

    def probe_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return self.check_auth(exe_path)

    def get_execution_profile(self) -> ExecutionProfile:
        return ExecutionProfile(
            mode=ExecutionMode.INTERACTIVE_TTY,
            command=[self.command],
            arguments_template=["-p", "{prompt}"],
            stdin_mode="PIPE",
            timeout_seconds=60
        )

    def get_test_invocation(self, exe_path: str, prompt: str, provider_id: Optional[str] = None) -> List[str]:
        return [exe_path, "-p", prompt]

    def get_capabilities(self, exe_path: str, operational: bool = False) -> Dict[str, str]:
        has_conpty = check_conpty_support()
        return {
            "chat": CapabilityStatus.DETECTED.value,
            "code": CapabilityStatus.DETECTED.value,
            "coding": CapabilityStatus.DETECTED.value,
            "file_read": CapabilityStatus.DETECTED.value,
            "file_write": CapabilityStatus.DETECTED.value,
            "shell": CapabilityStatus.DETECTED.value,
            "mcp": CapabilityStatus.DETECTED.value,
            "cancellation": CapabilityStatus.VERIFIED.value,
            "non_interactive": CapabilityStatus.UNSUPPORTED.value,
            "interactive_tty": CapabilityStatus.VERIFIED.value if has_conpty else CapabilityStatus.UNSUPPORTED.value
        }
