from typing import Dict, Any, Tuple, List, Optional
from .base import (
    BaseAgentAdapter, CapabilityStatus, ExecutionProfile, ExecutionMode,
    normalize_capability_matrix
)

class AntigravityAdapter(BaseAgentAdapter):
    id = "agy"
    name = "Antigravity CLI"
    command = "agy"
    provider = "antigravity"
    default_roles = ["ORCHESTRATOR", "PLANNER", "CODER", "REVIEWER"]

    def check_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return "AUTHENTICATED", {
            "auth_type": "antigravity_cli_session",
            "auth_check": "PASS"
        }

    def probe_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return self.check_auth(exe_path)

    def get_execution_profile(self) -> ExecutionProfile:
        return ExecutionProfile(
            mode=ExecutionMode.NON_INTERACTIVE,
            command=[self.command],
            arguments_template=["-p", "{prompt}"],
            stdin_mode="DEVNULL",
            timeout_seconds=600
        )

    def get_test_invocation(self, exe_path: str, prompt: str, provider_id: Optional[str] = None) -> List[str]:
        return [exe_path, "-p", prompt]

    def get_capabilities(self, exe_path: str, operational: bool = False) -> Dict[str, str]:
        st = CapabilityStatus.VERIFIED.value if operational else CapabilityStatus.DETECTED.value
        raw = {
            "chat": st,
            "code": st,
            "coding": st,
            "file_read": st,
            "file_write": st,
            "shell": st,
            "streaming": CapabilityStatus.VERIFIED.value,
            "cancellation": CapabilityStatus.VERIFIED.value,
            "mcp": CapabilityStatus.VERIFIED.value,
            "planning": st,
            "multi_agent": CapabilityStatus.VERIFIED.value,
            "orchestration": CapabilityStatus.VERIFIED.value,
            "browser": CapabilityStatus.UNKNOWN.value,
            "playwright": CapabilityStatus.UNKNOWN.value,
            "non_interactive": CapabilityStatus.VERIFIED.value,
            "image_vision": CapabilityStatus.UNKNOWN.value,
            "image_ingestion": CapabilityStatus.UNSUPPORTED.value,
            "ocr": CapabilityStatus.UNSUPPORTED.value,
            "pdf": CapabilityStatus.UNSUPPORTED.value,
            "docx": CapabilityStatus.UNSUPPORTED.value,
            "xlsx": CapabilityStatus.UNSUPPORTED.value,
            "pptx": CapabilityStatus.UNSUPPORTED.value,
            "document_text": CapabilityStatus.UNKNOWN.value,
            "interactive_tty": CapabilityStatus.UNKNOWN.value,
        }
        return normalize_capability_matrix(raw, operational=operational)

