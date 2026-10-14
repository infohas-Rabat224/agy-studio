import json
from typing import Dict, Any, Tuple, List, Optional
from .base import (
    BaseAgentAdapter, CapabilityStatus, ExecutionProfile, ExecutionMode,
    safe_run_process, normalize_capability_matrix
)

class ClaudeAdapter(BaseAgentAdapter):
    id = "claude"
    name = "Claude Code CLI"
    command = "claude"
    provider = "anthropic"
    default_roles = ["REVIEWER", "CODER", "DOCUMENTATION"]

    def _check_local_gateway(self) -> Tuple[bool, Optional[str]]:
        """Checks if Claude Code is configured to use a local proxy/gateway that is currently unreachable."""
        import os
        import socket
        from pathlib import Path
        try:
            from urllib.parse import urlparse
        except ImportError:
            return False, None

        urls_to_check = []
        base_env = os.environ.get("ANTHROPIC_BASE_URL")
        if base_env:
            urls_to_check.append(base_env)

        settings_path = Path.home() / ".claude" / "settings.json"
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    env_url = cfg.get("env", {}).get("ANTHROPIC_BASE_URL")
                    if env_url:
                        urls_to_check.append(env_url)
                    api_url = cfg.get("apiBaseUrl")
                    if api_url:
                        urls_to_check.append(api_url)
            except Exception:
                pass

        for u in urls_to_check:
            if "127.0.0.1" in u or "localhost" in u:
                try:
                    parsed = urlparse(u)
                    host = parsed.hostname or "127.0.0.1"
                    port = parsed.port or (443 if parsed.scheme == "https" else 80)
                    with socket.create_connection((host, port), timeout=0.8):
                        return False, u  # Online
                except Exception:
                    return True, u   # Offline
        return False, None

    def check_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        is_offline, proxy_url = self._check_local_gateway()
        if is_offline:
            return "AUTH_REQUIRED", {
                "auth_check": "FAIL",
                "error": f"Local AI Gateway at {proxy_url} is offline",
                "dependencies": {"nexus_gateway": "UNAVAILABLE"}
            }

        code, stdout, stderr, dur, _ = safe_run_process([exe_path, "auth", "status"], timeout=6)
        if code == 0:
            try:
                data = json.loads(stdout)
                if data.get("loggedIn"):
                    return "AUTHENTICATED", {
                        "auth_method": data.get("authMethod", "oauth"),
                        "api_provider": data.get("apiProvider", "anthropic"),
                        "auth_check": "PASS"
                    }
                return "AUTH_REQUIRED", {"auth_check": "FAIL", "details": "Not logged in"}
            except Exception:
                pass
            return "READY", {"auth_check": "PASS", "details": stdout[:100]}
        return "UNKNOWN", {"auth_check": "UNKNOWN", "details": stderr or stdout}

    def probe_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return self.check_auth(exe_path)

    def get_execution_profile(self) -> ExecutionProfile:
        return ExecutionProfile(
            mode=ExecutionMode.NON_INTERACTIVE,
            command=[self.command],
            arguments_template=["-p", "{prompt}", "--no-session-persistence"],
            stdin_mode="DEVNULL",
            timeout_seconds=60
        )

    def get_test_invocation(self, exe_path: str, prompt: str, provider_id: Optional[str] = None) -> List[str]:
        return [exe_path, "-p", prompt, "--no-session-persistence"]

    def get_capabilities(self, exe_path: str, operational: bool = False) -> Dict[str, str]:
        st = CapabilityStatus.VERIFIED.value if operational else CapabilityStatus.DETECTED.value
        raw = {
            "chat": st,
            "code": st,
            "coding": st,
            "file_read": st,
            "file_write": st,
            "shell": st,
            "git": st,
            "streaming": CapabilityStatus.VERIFIED.value,
            "cancellation": CapabilityStatus.VERIFIED.value,
            "mcp": CapabilityStatus.DETECTED.value,
            "planning": st,
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

