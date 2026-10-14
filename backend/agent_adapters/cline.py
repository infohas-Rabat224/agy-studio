from typing import Dict, Any, Tuple, List, Optional
from .base import (
    BaseAgentAdapter, CapabilityStatus, ExecutionProfile, ExecutionMode,
    safe_run_process, check_conpty_support, normalize_capability_matrix
)

class ClineAdapter(BaseAgentAdapter):
    id = "cline"
    name = "Cline CLI"
    command = "cline"
    provider = "cline"
    default_roles = ["CODER", "TESTER"]

    def check_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        code, stdout, stderr, _, _ = safe_run_process([exe_path, "doctor"], timeout=6)
        if code == 0:
            return "AVAILABLE", {
                "auth_check": "PASS",
                "details": "Cline doctor operational. Interactive TTY required for workflow sessions.",
                "conpty_supported": check_conpty_support()
            }
        return "UNKNOWN", {"auth_check": "UNKNOWN", "details": stderr}

    def probe_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return self.check_auth(exe_path)

    def get_execution_profile(self) -> ExecutionProfile:
        return ExecutionProfile(
            mode=ExecutionMode.INTERACTIVE_TTY,
            command=[self.command],
            arguments_template=["{prompt}", "--auto-approve", "true"],
            stdin_mode="PIPE",
            timeout_seconds=60
        )

    def get_test_invocation(self, exe_path: str, prompt: str, provider_id: Optional[str] = None) -> List[str]:
        return [exe_path, prompt, "--auto-approve", "true"]

    def get_capabilities(self, exe_path: str, operational: bool = False) -> Dict[str, str]:
        has_conpty = check_conpty_support()
        st = CapabilityStatus.VERIFIED.value if operational else CapabilityStatus.DETECTED.value
        raw = {
            "chat": st,
            "code": st,
            "coding": st,
            "file_read": st,
            "file_write": st,
            "shell": st,
            "mcp": CapabilityStatus.DETECTED.value,
            "cancellation": CapabilityStatus.VERIFIED.value,
            "non_interactive": CapabilityStatus.UNSUPPORTED.value,
            "interactive_tty": CapabilityStatus.VERIFIED.value if has_conpty else CapabilityStatus.UNSUPPORTED.value,
            "image_vision": CapabilityStatus.UNSUPPORTED.value,
            "image_ingestion": CapabilityStatus.UNSUPPORTED.value,
            "ocr": CapabilityStatus.UNSUPPORTED.value,
            "pdf": CapabilityStatus.UNSUPPORTED.value,
            "docx": CapabilityStatus.UNSUPPORTED.value,
            "xlsx": CapabilityStatus.UNSUPPORTED.value,
            "pptx": CapabilityStatus.UNSUPPORTED.value,
            "document_text": CapabilityStatus.UNKNOWN.value,
        }
        return normalize_capability_matrix(raw, operational=operational)

