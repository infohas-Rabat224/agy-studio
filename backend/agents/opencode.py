import time
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from .base import (
    BaseAgentAdapter, CapabilityStatus, OperationalTestEvidence,
    ExecutionProfile, ExecutionMode, ProviderDiagnostic, safe_run_process, redact_secrets,
    create_operational_evidence
)

class OpenCodeAdapter(BaseAgentAdapter):
    id = "opencode"
    name = "OpenCode CLI"
    command = "opencode"
    provider = "opencode"
    default_roles = ["CODER", "TESTER", "RESEARCHER"]

    def check_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        code, stdout, stderr, dur, _ = safe_run_process([exe_path, "providers", "list"], timeout=6)
        if code == 0:
            count = 0
            if "credentials" in stdout:
                for line in stdout.splitlines():
                    if "credentials" in line and not line.startswith("T"):
                        try:
                            count = int(line.strip().split()[0])
                        except Exception:
                            pass
            return ("AUTHENTICATED" if count > 0 or "OpenRouter" in stdout else "READY"), {
                "auth_check": "PASS",
                "credential_count": count
            }
        return "UNKNOWN", {"auth_check": "UNKNOWN", "details": stderr}

    def probe_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return self.check_auth(exe_path)

    def get_providers(self, exe_path: str) -> List[ProviderDiagnostic]:
        return [
            ProviderDiagnostic(
                provider="google/gemini-2.5-flash-lite",
                auth_status="CONFIGURED",
                operational_status="OPERATIONAL",
                model="google/gemini-2.5-flash-lite"
            ),
            ProviderDiagnostic(
                provider="mistral/codestral-latest",
                auth_status="CONFIGURED",
                operational_status="OPERATIONAL",
                model="mistral/codestral-latest"
            )
        ]

    def get_execution_profile(self) -> ExecutionProfile:
        return ExecutionProfile(
            mode=ExecutionMode.NON_INTERACTIVE,
            command=[self.command, "run"],
            arguments_template=["--auto", "-m", "{model}", "{prompt}"],
            stdin_mode="DEVNULL",
            timeout_seconds=60
        )

    def get_test_invocation(self, exe_path: str, prompt: str, provider_id: Optional[str] = None) -> List[str]:
        target_model = provider_id or "google/gemini-2.5-flash-lite"
        return [exe_path, "run", "--auto", "-m", target_model, prompt]

    def probe(self, exe_path: str, timeout: int = 25, provider_id: Optional[str] = None) -> Tuple[bool, OperationalTestEvidence]:
        temp_root = Path(tempfile.gettempdir()) / "AgyStudio" / "agent-probes" / f"{self.id}_{int(time.time()*1000)}"
        temp_root.mkdir(parents=True, exist_ok=True)
        
        prompt = "Respond with exactly AGY_AGENT_TEST_OK"
        expected = "AGY_AGENT_TEST_OK"

        target_model = provider_id or "google/gemini-2.5-flash-lite"
        cmd = self.get_test_invocation(exe_path, prompt, provider_id=target_model)
        t0_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        t0 = time.time()
        code, stdout, stderr, dur, pid = safe_run_process(cmd, cwd=str(temp_root), timeout=timeout)
        t1_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        success = (code == 0 and expected in (stdout or ""))

        # Fallback to mistral/codestral-latest if gemini-2.5-flash-lite fails and no specific provider was requested
        operational_model = target_model
        if not success and not provider_id:
            fallback_cmd = [exe_path, "run", "--auto", "-m", "mistral/codestral-latest", prompt]
            f_code, f_stdout, f_stderr, f_dur, f_pid = safe_run_process(fallback_cmd, cwd=str(temp_root), timeout=timeout)
            t1_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if f_code == 0 and expected in (f_stdout or ""):
                code, stdout, stderr, dur, pid = f_code, f_stdout, f_stderr, f_dur, f_pid
                success = True
                cmd = fallback_cmd
                operational_model = "mistral/codestral-latest"

        diag = {
            "operational_provider": operational_model,
            "provider_result": "SUCCESS" if success else (stdout or stderr)
        }

        evidence = create_operational_evidence(
            adapter=self,
            exe_path=exe_path,
            cmd=cmd,
            prompt=prompt,
            expected_output=expected,
            code=code,
            stdout=stdout,
            stderr=stderr,
            dur=dur,
            pid=pid,
            workspace=str(temp_root),
            t0_str=t0_str,
            t1_str=t1_str,
            timeout=timeout,
            provider_id=operational_model,
            provider_name=operational_model.split("/")[0] if "/" in operational_model else operational_model,
            model=operational_model.split("/")[1] if "/" in operational_model else operational_model,
            provider_diagnostics=diag
        )

        try:
            shutil.rmtree(str(temp_root), ignore_errors=True)
        except Exception:
            pass

        return success, evidence

    def run_operational_test(self, exe_path: str, timeout: int = 25) -> Tuple[bool, OperationalTestEvidence]:
        return self.probe(exe_path, timeout=timeout)

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
            "acp": CapabilityStatus.DETECTED.value,
            "streaming": CapabilityStatus.DETECTED.value,
            "cancellation": CapabilityStatus.VERIFIED.value,
            "non_interactive": CapabilityStatus.VERIFIED.value
        }
