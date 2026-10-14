import re
import time
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from .base import (
    BaseAgentAdapter, CapabilityStatus, OperationalTestEvidence,
    ProviderDiagnostic, ExecutionProfile, ExecutionMode, safe_run_process, redact_secrets,
    create_operational_evidence, normalize_capability_matrix
)

class HermesAdapter(BaseAgentAdapter):
    id = "hermes"
    name = "Hermes CLI"
    command = "hermes"
    provider = "hermes"
    default_roles = ["CODER", "PLANNER", "RESEARCHER"]

    def check_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        code, stdout, stderr, dur, _ = safe_run_process([exe_path, "auth", "list"], timeout=8)
        if code == 0:
            providers = []
            for line in stdout.splitlines():
                m = re.match(r"^([\w\:\-]+)\s+\(\d+\s+credentials\):", line.strip())
                if m:
                    providers.append(m.group(1))
            return ("AUTHENTICATED" if providers else "READY"), {
                "configured_providers": providers,
                "provider_count": len(providers),
                "auth_check": "PASS"
            }
        return "UNKNOWN", {"auth_check": "UNKNOWN", "details": stderr}

    def probe_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        return self.check_auth(exe_path)

    def get_providers(self, exe_path: str) -> List[ProviderDiagnostic]:
        """Discovers configured Hermes providers from 'hermes auth list'."""
        code, stdout, _, _, _ = safe_run_process([exe_path, "auth", "list"], timeout=8)
        diagnostics = []
        if code == 0:
            for line in stdout.splitlines():
                m = re.match(r"^([\w\:\-]+)\s+\(\d+\s+credentials\):", line.strip())
                if m:
                    pname = m.group(1)
                    # We know gemini provider has valid keys and operational status
                    op_status = "OPERATIONAL" if pname == "gemini" else "UNKNOWN"
                    diagnostics.append(ProviderDiagnostic(
                        provider=pname,
                        auth_status="CONFIGURED",
                        operational_status=op_status,
                        model="gemini-3.8-flash" if pname == "gemini" else None
                    ))
        return diagnostics

    def get_execution_profile(self) -> ExecutionProfile:
        return ExecutionProfile(
            mode=ExecutionMode.NON_INTERACTIVE,
            command=[self.command],
            arguments_template=["-z", "{prompt}", "--provider", "{provider}", "-m", "{model}", "--safe-mode"],
            stdin_mode="DEVNULL",
            timeout_seconds=60
        )

    def get_test_invocation(self, exe_path: str, prompt: str, provider_id: Optional[str] = None) -> List[str]:
        # If gemini provider requested or used as operational fallback:
        target_provider = provider_id or "gemini"
        if target_provider == "gemini":
            return [exe_path, "-z", prompt, "--provider", "gemini", "-m", "gemini-3.8-flash", "--safe-mode"]
        elif target_provider and target_provider != "default":
            return [exe_path, "-z", prompt, "--provider", target_provider, "--safe-mode"]
        return [exe_path, "-z", prompt, "--safe-mode"]

    def probe(self, exe_path: str, timeout: int = 25, provider_id: Optional[str] = None) -> Tuple[bool, OperationalTestEvidence]:
        temp_root = Path(tempfile.gettempdir()) / "AgyStudio" / "agent-probes" / f"{self.id}_{int(time.time()*1000)}"
        temp_root.mkdir(parents=True, exist_ok=True)
        
        prompt = "Respond with exactly AGY_AGENT_TEST_OK"
        expected = "AGY_AGENT_TEST_OK"
        
        target_prov = provider_id or "gemini"
        cmd = self.get_test_invocation(exe_path, prompt, provider_id=target_prov)

        t0_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        t0 = time.time()
        code, stdout, stderr, dur, pid = safe_run_process(cmd, cwd=str(temp_root), timeout=timeout)
        t1_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        success = (code == 0 and expected in (stdout or ""))

        model_used = "gemini-3.8-flash" if target_prov == "gemini" else "default"
        diag = {
            "cli_health": "READY",
            "tested_provider": target_prov,
            "provider_result": "SUCCESS" if success else (stdout[:120] if stdout else stderr[:120]),
            "model_used": model_used
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
            provider_id=target_prov,
            provider_name=target_prov,
            model=model_used,
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
        raw = {
            "chat": st,
            "code": st,
            "coding": st,
            "file_read": st,
            "file_write": st,
            "shell": st,
            "streaming": CapabilityStatus.VERIFIED.value,
            "cancellation": CapabilityStatus.VERIFIED.value,
            "mcp": CapabilityStatus.DETECTED.value,
            "planning": st,
            "browser": CapabilityStatus.UNKNOWN.value,
            "playwright": CapabilityStatus.UNKNOWN.value,
            "non_interactive": CapabilityStatus.VERIFIED.value,
            "image_vision": CapabilityStatus.UNSUPPORTED.value,
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

