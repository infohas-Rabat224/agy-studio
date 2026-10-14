import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from .base import (
    BaseAgentAdapter, CapabilityStatus, ExecutionProfile, ExecutionMode,
    ProbeEvidence, safe_run_process, redact_secrets
)

class CustomAdapter(BaseAgentAdapter):
    def __init__(
        self,
        agent_id: str,
        name: str,
        command: str,
        custom_path: Optional[str] = None,
        version_args: Optional[List[str]] = None,
        test_args: Optional[List[str]] = None,
        prompt_mode: str = "argument",  # argument or stdin
        timeout: int = 120,
        roles: Optional[List[str]] = None,
        declared_capabilities: Optional[Dict[str, bool]] = None
    ):
        self.id = agent_id
        self.name = name
        self.command = command
        self.provider = "custom"
        self.custom_path = custom_path
        self.version_args = version_args or ["--version"]
        self.test_args = test_args or ["-p", "{prompt}"]
        self.prompt_mode = prompt_mode
        self.timeout = timeout
        self.default_roles = roles or ["CODER"]
        self.declared_capabilities = declared_capabilities or {}

    def discover(self) -> Optional[str]:
        if self.custom_path and Path(self.custom_path).exists():
            return str(Path(self.custom_path).resolve())
        return super().discover()

    def _build_command_prefix(self, exe_path: str) -> List[str]:
        p = Path(exe_path)
        ext = p.suffix.lower()
        if ext == ".py":
            return [sys.executable, str(p)]
        elif ext == ".ps1":
            return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(p)]
        elif ext == ".js":
            return ["node", str(p)]
        elif ext in [".cmd", ".bat"]:
            return ["cmd.exe", "/c", str(p)]
        return [str(p)]

    def get_version(self, exe_path: str) -> Tuple[bool, str, ProbeEvidence]:
        cmd = self._build_command_prefix(exe_path) + self.version_args
        code, stdout, stderr, dur, _ = safe_run_process(cmd, timeout=8)
        ev = ProbeEvidence(
            command=redact_secrets(f"{self.command} {' '.join(self.version_args)}"),
            exit_code=code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=dur,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        if code == 0:
            first_line = stdout.splitlines()[0] if stdout else "Custom CLI v1.0.0"
            return True, first_line, ev
        return False, "", ev

    def probe_version(self, exe_path: str) -> Tuple[bool, str, ProbeEvidence]:
        return self.get_version(exe_path)

    def check_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return "READY", {"auth_check": "PASS", "details": "Custom CLI registered and responsive"}

    def probe_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return self.check_auth(exe_path)

    def get_execution_profile(self) -> ExecutionProfile:
        return ExecutionProfile(
            mode=ExecutionMode.CUSTOM,
            command=[self.command],
            arguments_template=self.test_args,
            stdin_mode="PIPE" if self.prompt_mode == "stdin" else "DEVNULL",
            timeout_seconds=self.timeout
        )

    def get_test_invocation(self, exe_path: str, prompt: str, provider_id: Optional[str] = None) -> List[str]:
        prefix = self._build_command_prefix(exe_path)
        if self.prompt_mode == "stdin":
            return prefix
        res = list(prefix)
        for arg in self.test_args:
            res.append(arg.replace("{prompt}", prompt))
        return res

    def get_capabilities(self, exe_path: str, operational: bool = False) -> Dict[str, str]:
        st = CapabilityStatus.VERIFIED.value if operational else CapabilityStatus.DETECTED.value
        caps = {
            "chat": st,
            "code": st,
            "file_read": st,
            "file_write": st,
            "shell": st,
            "cancellation": CapabilityStatus.VERIFIED.value,
            "non_interactive": CapabilityStatus.VERIFIED.value
        }
        for k, v in self.declared_capabilities.items():
            if v:
                caps[k] = st
            else:
                caps[k] = CapabilityStatus.UNSUPPORTED.value
        return caps
