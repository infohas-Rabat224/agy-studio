import os
import sys
import re
import time
import shutil
import tempfile
import subprocess
import hashlib
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Iterator
from pydantic import BaseModel, Field

# ============================================================================
# UNIVERSAL AGENT STATUS & CAPABILITY SEMANTICS
# ============================================================================

class AgentStatus(str, Enum):
    NOT_INSTALLED = "NOT_INSTALLED"     # Not found on machine / PATH
    DISCOVERED = "DISCOVERED"           # Binary found on disk / PATH
    AVAILABLE = "AVAILABLE"             # Binary responds to version/help
    AUTH_REQUIRED = "AUTH_REQUIRED"     # Needs authentication / API credentials
    AUTHENTICATED = "AUTHENTICATED"     # Auth check succeeded
    READY = "READY"                     # Ready for operational probe
    OPERATIONAL = "OPERATIONAL"         # Passed live capability probe with verified output
    STALE = "STALE"                     # Previously verified but verification expired
    BUSY = "BUSY"                       # Currently executing real task
    DEGRADED = "DEGRADED"               # Operational test had warnings/partial failure
    FAILED = "FAILED"                   # Operational test failed
    DISABLED = "DISABLED"               # Disabled by user

class CapabilityStatus(str, Enum):
    VERIFIED = "VERIFIED"               # Proven via live probe
    DETECTED = "DETECTED"               # Inferred from flags / schemas
    UNKNOWN = "UNKNOWN"                 # Not verified
    UNSUPPORTED = "UNSUPPORTED"         # Explicitly unsupported (e.g. headless on TTY-only CLI)

class ExecutionMode(str, Enum):
    NON_INTERACTIVE = "NON_INTERACTIVE" # Standard headless execution
    INTERACTIVE_TTY = "INTERACTIVE_TTY" # Requires pseudo-terminal / ConPTY
    STREAMING = "STREAMING"             # Real-time stdout/stderr chunk streaming
    HTTP = "HTTP"                       # Local REST/daemon bridge
    CUSTOM = "CUSTOM"                   # User-defined execution profile

# ============================================================================
# SECRET REDACTION & SECURITY UTILITIES
# ============================================================================

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"AIza[A-Za-z0-9_-]{35}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
    re.compile(r"(api[_-]?key|password|secret)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9._-]{8,})[\"']?", re.IGNORECASE),
]

def redact_secrets(text: str) -> str:
    """Masks API keys, tokens, and credentials in execution logs and evidence."""
    if not text:
        return ""
    masked = str(text)
    for pat in SECRET_PATTERNS:
        def _repl(match):
            val = match.group(0)
            if len(val) <= 8:
                return "********"
            prefix = val[:4]
            suffix = val[-4:]
            return f"{prefix}****{suffix}"
        masked = pat.sub(_repl, masked)
    return masked

def kill_process_tree(pid: int) -> bool:
    """Safely kills a process tree on Windows and verifies termination."""
    if not pid:
        return True
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=5)
        else:
            import signal
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        time.sleep(0.2)
        # Verify process is gone
        if sys.platform == "win32":
            chk = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
            return str(pid) not in chk.stdout
        return True
    except Exception:
        return False

def check_conpty_support() -> bool:
    """Detects whether Windows ConPTY (CreatePseudoConsole) is supported on this host."""
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        return hasattr(ctypes.windll.kernel32, "CreatePseudoConsole")
    except Exception:
        return False

# ============================================================================
# DATA & EVIDENCE MODELS
# ============================================================================

class VerificationFailureReason(str, Enum):
    PROBE_FAILURE = "PROBE_FAILURE"
    TASK_FAILURE = "TASK_FAILURE"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    AUTH_FAILURE = "AUTH_FAILURE"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    CONFIGURATION_FAILURE = "CONFIGURATION_FAILURE"
    PROCESS_FAILURE = "PROCESS_FAILURE"

class ExecutableIdentity(BaseModel):
    agent_id: str
    executable_path: str
    resolved_executable_path: str
    version: Optional[str] = None
    file_size: int = 0
    file_mtime: float = 0.0
    optional_sha256: Optional[str] = None
    verified_at: Optional[str] = None
    verification_duration: int = 0
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None
    model: Optional[str] = None
    verified_capabilities: List[str] = Field(default_factory=list)

class CapabilityEvidence(BaseModel):
    capability: str
    status: str                         # VERIFIED, UNSUPPORTED, UNKNOWN
    verified_at: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    evidence_execution_id: Optional[str] = None

class ProbeEvidence(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timestamp: str

class ProviderDiagnostic(BaseModel):
    provider: str
    auth_status: str
    operational_status: str
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    model: Optional[str] = None

class OperationalTestEvidence(BaseModel):
    execution_id: str = Field(default_factory=lambda: f"probe_{int(time.time()*1000)}")
    agent_id: str = ""
    test_name: str = "minimal_agent_task"
    prompt: str = "Respond with exactly AGY_AGENT_TEST_OK"
    expected_output: str = "AGY_AGENT_TEST_OK"
    actual_output: str = ""
    exit_code: int = 0
    duration_ms: int = 0
    success: bool = False
    error: Optional[str] = None
    failure_reason: Optional[str] = None
    workspace: str = ""
    timestamp: str = ""
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    pid: Optional[int] = None
    command: Optional[str] = None
    command_redacted: Optional[str] = None
    stdout_redacted: Optional[str] = None
    stderr_redacted: Optional[str] = None
    executable_path: Optional[str] = None
    resolved_executable_path: Optional[str] = None
    version: Optional[str] = None
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None
    model: Optional[str] = None
    executable_identity: Optional[ExecutableIdentity] = None
    configuration_fingerprint: Optional[str] = None
    capabilities: Dict[str, str] = Field(default_factory=dict)
    capability_evidences: Dict[str, CapabilityEvidence] = Field(default_factory=dict)
    artifact_paths: List[str] = Field(default_factory=list)
    verification_result: str = "PASS"  # PASS or FAIL
    provider_diagnostics: Optional[Dict[str, Any]] = None

class ExecutionProfile(BaseModel):
    mode: ExecutionMode = ExecutionMode.NON_INTERACTIVE
    command: List[str] = Field(default_factory=list)
    arguments_template: List[str] = Field(default_factory=list)
    stdin_mode: str = "DEVNULL"          # DEVNULL, PIPE, NONE
    environment: Dict[str, str] = Field(default_factory=dict)
    working_directory_mode: str = "workspace" # workspace, isolated, cwd
    timeout_seconds: int = 60

class TaskExecutionRequest(BaseModel):
    task_id: str
    agent_id: str
    provider_id: Optional[str] = None
    role: str = "CODER"
    workspace: str
    prompt: str
    required_capabilities: List[str] = Field(default_factory=list)
    timeout_seconds: int = 60
    stream: bool = False
    stdin_data: Optional[str] = None

class TaskExecutionResult(BaseModel):
    execution_id: str
    task_id: str
    agent_id: str
    provider_id: Optional[str] = None
    adapter: str
    command_redacted: str
    working_directory: str
    started_at: str
    ended_at: str
    duration_ms: int
    pid: Optional[int] = None
    exit_code: int
    status: str                         # SUCCESS, FAILED, TIMEOUT, CANCELLED
    failure_reason: Optional[str] = None
    stdout: str
    stderr: str
    artifacts: List[str] = Field(default_factory=list)
    capabilities_used: List[str] = Field(default_factory=list)
    selection_reason: Optional[str] = None
    failover_chain: List[str] = Field(default_factory=list)

class AgentModel(BaseModel):
    id: str
    name: str
    command: str
    path: Optional[str] = None
    version: Optional[str] = None
    provider: str
    status: AgentStatus = AgentStatus.NOT_INSTALLED
    last_checked: Optional[str] = None
    last_verified: Optional[str] = None
    verification_age_seconds: Optional[int] = None
    capabilities: Dict[str, str] = Field(default_factory=dict)
    capability_evidences: Dict[str, CapabilityEvidence] = Field(default_factory=dict)
    health: Dict[str, Any] = Field(default_factory=dict)
    authentication: Dict[str, Any] = Field(default_factory=dict)
    execution: Dict[str, Any] = Field(default_factory=dict)
    execution_profile: Optional[ExecutionProfile] = None
    limits: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    version_evidence: Optional[ProbeEvidence] = None
    operational_evidence: Optional[OperationalTestEvidence] = None
    executable_identity: Optional[ExecutableIdentity] = None
    configuration_fingerprint: Optional[str] = None
    provider_diagnostics: Optional[Dict[str, Any]] = None
    configured_providers: List[ProviderDiagnostic] = Field(default_factory=list)
    active_provider: Optional[str] = None
    is_custom: bool = False

def get_executable_identity(
    exe_path: str,
    agent_id: str,
    version: Optional[str] = None,
    provider_id: Optional[str] = None,
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    verified_capabilities: Optional[List[str]] = None,
    verification_duration: int = 0
) -> ExecutableIdentity:
    p = Path(exe_path).resolve()
    size = 0
    mtime = 0.0
    sha = None
    if p.exists() and p.is_file():
        st = p.stat()
        size = st.st_size
        mtime = st.st_mtime
        try:
            with open(p, "rb") as f:
                sha = hashlib.sha256(f.read(1024 * 1024)).hexdigest()
        except Exception:
            pass
    return ExecutableIdentity(
        agent_id=agent_id,
        executable_path=str(exe_path),
        resolved_executable_path=str(p),
        version=version,
        file_size=size,
        file_mtime=mtime,
        optional_sha256=sha,
        verified_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        verification_duration=verification_duration,
        provider_id=provider_id,
        provider_name=provider_name,
        model=model,
        verified_capabilities=verified_capabilities or []
    )

def is_executable_identity_valid(identity: Optional[ExecutableIdentity], exe_path: str) -> Tuple[bool, str]:
    if not identity:
        return False, "No executable identity recorded in verification evidence."
    p = Path(exe_path).resolve()
    if not p.exists() or not p.is_file():
        return False, f"Executable file no longer exists at '{p}'."
    st = p.stat()
    if st.st_size != identity.file_size:
        return False, f"Executable file size changed ({st.st_size} bytes != recorded {identity.file_size} bytes)."
    if abs(st.st_mtime - identity.file_mtime) > 0.01:
        if identity.optional_sha256:
            try:
                with open(p, "rb") as f:
                    curr_sha = hashlib.sha256(f.read(1024 * 1024)).hexdigest()
                if curr_sha != identity.optional_sha256:
                    return False, f"Executable binary SHA256 checksum changed ({curr_sha[:10]}... != {identity.optional_sha256[:10]}...)."
            except Exception:
                return False, f"Executable timestamp changed ({st.st_mtime} != {identity.file_mtime})."
        else:
            return False, f"Executable timestamp changed ({st.st_mtime} != {identity.file_mtime})."
    return True, "Executable identity matches verified baseline."

def compute_config_fingerprint(
    exe_identity: Optional[ExecutableIdentity],
    version: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    execution_mode: str,
    relevant_capabilities: List[str]
) -> str:
    components = [
        exe_identity.resolved_executable_path if exe_identity else "",
        str(exe_identity.file_size) if exe_identity else "",
        str(exe_identity.file_mtime) if exe_identity else "",
        str(exe_identity.optional_sha256) if exe_identity else "",
        str(version or ""),
        str(provider or ""),
        str(model or ""),
        str(execution_mode or ""),
        ",".join(sorted(relevant_capabilities))
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def create_operational_evidence(
    adapter: "BaseAgentAdapter",
    exe_path: str,
    cmd: List[str],
    prompt: str,
    expected_output: str,
    code: int,
    stdout: str,
    stderr: str,
    dur: int,
    pid: Optional[int],
    workspace: str,
    t0_str: str,
    t1_str: str,
    timeout: int,
    provider_id: Optional[str] = None,
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    provider_diagnostics: Optional[Dict[str, Any]] = None,
    artifact_paths: Optional[List[str]] = None
) -> OperationalTestEvidence:
    success = (code == 0 and expected_output in (stdout or ""))
    error = None
    failure_reason = None
    if not success:
        err_msg = stderr or (f"Output '{stdout[:100]}' did not match '{expected_output}'" if stdout else "No output")
        error = err_msg
        if dur >= timeout * 1000 or "timed out" in err_msg.lower():
            failure_reason = VerificationFailureReason.TIMEOUT.value
        elif "401" in err_msg or "unauthorized" in err_msg.lower() or "auth" in err_msg.lower():
            failure_reason = VerificationFailureReason.AUTH_FAILURE.value
        elif "429" in err_msg or "quota" in err_msg.lower() or "rate" in err_msg.lower():
            failure_reason = VerificationFailureReason.PROVIDER_FAILURE.value
        elif "syntax" in err_msg.lower() or "config" in err_msg.lower():
            failure_reason = VerificationFailureReason.CONFIGURATION_FAILURE.value
        else:
            failure_reason = VerificationFailureReason.PROBE_FAILURE.value

    ok_v, ver_str, _ = adapter.get_version(exe_path)
    version_val = ver_str if ok_v else None

    target_prov = provider_id or adapter.provider
    caps = adapter.get_capabilities(exe_path, operational=success)
    verified_caps = [c for c, st in caps.items() if st == CapabilityStatus.VERIFIED.value]

    exe_ident = get_executable_identity(
        exe_path=exe_path,
        agent_id=adapter.id,
        version=version_val,
        provider_id=target_prov,
        provider_name=provider_name or target_prov,
        model=model,
        verified_capabilities=verified_caps,
        verification_duration=dur
    )

    prof = adapter.get_execution_profile()
    config_fp = compute_config_fingerprint(
        exe_identity=exe_ident,
        version=version_val,
        provider=target_prov,
        model=model,
        execution_mode=prof.mode.value,
        relevant_capabilities=verified_caps
    )

    exec_id = f"probe_{adapter.id}_{int(time.time()*1000)}"
    cap_evidences = {}
    for c_key, c_st in caps.items():
        cap_evidences[c_key] = CapabilityEvidence(
            capability=c_key,
            status=c_st,
            verified_at=t1_str if c_st == CapabilityStatus.VERIFIED.value else None,
            provider=target_prov if c_st == CapabilityStatus.VERIFIED.value else None,
            model=model if c_st == CapabilityStatus.VERIFIED.value else None,
            evidence_execution_id=exec_id if c_st == CapabilityStatus.VERIFIED.value else None
        )

    return OperationalTestEvidence(
        execution_id=exec_id,
        agent_id=adapter.id,
        test_name="minimal_agent_task",
        prompt=prompt,
        expected_output=expected_output,
        actual_output=stdout or "",
        exit_code=code,
        duration_ms=dur,
        success=success,
        error=error,
        failure_reason=failure_reason,
        workspace=str(workspace),
        timestamp=t1_str,
        started_at=t0_str,
        ended_at=t1_str,
        pid=pid,
        command=redact_secrets(" ".join(cmd)),
        command_redacted=redact_secrets(" ".join(cmd)),
        stdout_redacted=redact_secrets(stdout or ""),
        stderr_redacted=redact_secrets(stderr or ""),
        executable_path=str(exe_path),
        resolved_executable_path=str(Path(exe_path).resolve()),
        version=version_val,
        provider_id=target_prov,
        provider_name=provider_name or target_prov,
        model=model,
        executable_identity=exe_ident,
        configuration_fingerprint=config_fp,
        capabilities=caps,
        capability_evidences=cap_evidences,
        artifact_paths=artifact_paths or [],
        verification_result="PASS" if success else "FAIL",
        provider_diagnostics=provider_diagnostics
    )

# ============================================================================
# SUBPROCESS EXECUTION ENGINE
# ============================================================================

def safe_run_process(
    args: List[str],
    cwd: Optional[str] = None,
    timeout: int = 15,
    stdin_data: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Tuple[int, str, str, int, Optional[int]]:
    """
    Safely executes a process on Windows handling .cmd/.bat wrappers,
    avoiding shell injection, measuring duration in ms, and capturing PID.
    Cleanly kills the process tree on timeout. Redacts secrets from errors.
    """
    if not args:
        return -1, "", "No command provided", 0, None

    cmd_args = list(args)
    exe = cmd_args[0]
    is_batch = exe.lower().endswith(".cmd") or exe.lower().endswith(".bat")
    
    if is_batch:
        final_cmd = ["cmd.exe", "/c"] + cmd_args
    else:
        final_cmd = cmd_args

    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    t0 = time.time()
    proc = None
    try:
        proc = subprocess.Popen(
            final_cmd,
            cwd=cwd,
            env=run_env,
            stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        pid = proc.pid
        stdout, stderr = proc.communicate(input=stdin_data, timeout=timeout)
        duration_ms = int((time.time() - t0) * 1000)
        return proc.returncode, redact_secrets(stdout or "").strip(), redact_secrets(stderr or "").strip(), duration_ms, pid
    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - t0) * 1000)
        pid = proc.pid if proc else None
        if pid:
            kill_process_tree(pid)
        if proc:
            try:
                proc.kill()
                proc.wait(timeout=1)
            except Exception:
                pass
        return -1, "", f"Execution timed out after {timeout} seconds", duration_ms, pid
    except Exception as ex:
        duration_ms = int((time.time() - t0) * 1000)
        pid = proc.pid if proc else None
        if pid:
            kill_process_tree(pid)
        if proc:
            try:
                proc.kill()
                proc.wait(timeout=1)
            except Exception:
                pass
        return -1, "", redact_secrets(str(ex)), duration_ms, pid

# ============================================================================
# UNIVERSAL BASE AGENT ADAPTER CONTRACT
# ============================================================================

class BaseAgentAdapter:
    """
    Universal Contract for ALL AI CLI Agents.
    Normalizes invocation differences (EXE, CMD, BAT, PS1, Node, Python, Rust, Go, Custom).
    The orchestrator interacts ONLY with this contract and never performs provider branching.
    """
    id: str = ""
    name: str = ""
    command: str = ""
    provider: str = ""
    default_roles: List[str] = []

    def discover(self) -> Optional[str]:
        """Discover executable path safely and dynamically across PATH and standard user locations."""
        found = shutil.which(self.command)
        if found:
            return found
        # Dynamic search in host user directories
        local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
        roaming = Path(os.environ.get("APPDATA", ""))
        user_profile = Path(os.environ.get("USERPROFILE", ""))
        
        candidates = [
            local_app_data / self.command / "bin" / f"{self.command}.exe",
            local_app_data / self.command / "bin" / f"{self.command}.cmd",
            local_app_data / "Programs" / self.command / "bin" / f"{self.command}.exe",
            roaming / "npm" / f"{self.command}.cmd",
            user_profile / ".local" / "bin" / f"{self.command}.exe",
            user_profile / ".local" / "bin" / f"{self.command}.cmd"
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        return None

    def get_version(self, exe_path: str) -> Tuple[bool, str, ProbeEvidence]:
        """Runs the CLI version command and captures forensic evidence."""
        code, stdout, stderr, dur, _ = safe_run_process([exe_path, "--version"], timeout=8)
        ev = ProbeEvidence(
            command=f"{self.command} --version",
            exit_code=code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=dur,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        if code == 0:
            first_line = stdout.splitlines()[0] if stdout else "Unknown Version"
            return True, first_line, ev
        return False, "", ev

    def probe_version(self, exe_path: str) -> Tuple[bool, str, ProbeEvidence]:
        """Backward-compatible alias for get_version."""
        return self.get_version(exe_path)

    def check_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        """Safe non-destructive auth check."""
        return "UNKNOWN", {"details": "No dedicated auth probe"}

    def probe_auth(self, exe_path: str) -> Tuple[str, Dict[str, Any]]:
        """Backward-compatible alias for check_auth."""
        return self.check_auth(exe_path)

    def get_capabilities(self, exe_path: str, operational: bool = False) -> Dict[str, str]:
        """Returns capabilities with VERIFIED, DETECTED, UNKNOWN, or UNSUPPORTED."""
        return {}

    def get_providers(self, exe_path: str) -> List[ProviderDiagnostic]:
        """Returns discovered providers and their diagnostic health for multi-provider CLIs."""
        return []

    def get_execution_profile(self) -> ExecutionProfile:
        """Returns the execution profile (mode, arguments, flags, stdin policy)."""
        return ExecutionProfile(
            mode=ExecutionMode.NON_INTERACTIVE,
            command=[self.command],
            arguments_template=["-p", "{prompt}"],
            stdin_mode="DEVNULL"
        )

    def get_test_invocation(self, exe_path: str, prompt: str, provider_id: Optional[str] = None) -> List[str]:
        """Returns the structured arguments to execute a single prompt non-interactively."""
        return [exe_path, "-p", prompt]

    def probe(self, exe_path: str, timeout: int = 25, provider_id: Optional[str] = None) -> Tuple[bool, OperationalTestEvidence]:
        """Executes a minimal test in isolated temporary workspace %TEMP%/AgyStudio/agent-probes/<id>."""
        temp_root = Path(tempfile.gettempdir()) / "AgyStudio" / "agent-probes" / f"{self.id}_{int(time.time()*1000)}"
        temp_root.mkdir(parents=True, exist_ok=True)
        
        prompt = "Respond with exactly AGY_AGENT_TEST_OK"
        expected = "AGY_AGENT_TEST_OK"
        cmd = self.get_test_invocation(exe_path, prompt, provider_id=provider_id)

        t0_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        t0 = time.time()
        code, stdout, stderr, dur, pid = safe_run_process(cmd, cwd=str(temp_root), timeout=timeout)
        t1_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

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
            provider_id=provider_id
        )

        try:
            shutil.rmtree(str(temp_root), ignore_errors=True)
        except Exception:
            pass

        return evidence.success, evidence

    def run_operational_test(self, exe_path: str, timeout: int = 25) -> Tuple[bool, OperationalTestEvidence]:
        """Backward-compatible alias for probe."""
        return self.probe(exe_path, timeout=timeout)

    def execute(self, req: TaskExecutionRequest) -> TaskExecutionResult:
        """Executes a task request according to this adapter's contract."""
        exe_path = self.discover()
        if not exe_path:
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            return TaskExecutionResult(
                execution_id=f"exec_{int(time.time())}",
                task_id=req.task_id,
                agent_id=self.id,
                provider_id=req.provider_id,
                adapter=self.__class__.__name__,
                command_redacted=self.command,
                working_directory=req.workspace,
                started_at=now,
                ended_at=now,
                duration_ms=0,
                exit_code=-1,
                status="FAILED",
                failure_reason=VerificationFailureReason.PROCESS_FAILURE.value,
                stdout="",
                stderr="Agent executable not discovered on system",
                artifacts=[]
            )

        cmd = self.get_test_invocation(exe_path, req.prompt, provider_id=req.provider_id)
        ws = Path(req.workspace)
        ws.mkdir(parents=True, exist_ok=True)

        # Baseline snapshot of artifacts in workspace before execution
        before_files = set(f.name for f in ws.iterdir()) if ws.exists() else set()
        
        t0_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        t0 = time.time()
        code, stdout, stderr, dur, pid = safe_run_process(
            cmd, cwd=str(ws), timeout=req.timeout_seconds, stdin_data=req.stdin_data
        )
        t1_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Detect newly created artifact files
        after_files = set(f.name for f in ws.iterdir()) if ws.exists() else set()
        new_artifacts = sorted(list(after_files - before_files))

        status_str = "SUCCESS" if code == 0 else "FAILED"
        fail_reason = None
        if code != 0:
            err_l = (stderr or stdout or "").lower()
            if "timed out" in err_l:
                fail_reason = VerificationFailureReason.TIMEOUT.value
            elif "cancelled" in err_l:
                fail_reason = VerificationFailureReason.CANCELLED.value
            elif "401" in err_l or "unauthorized" in err_l:
                fail_reason = VerificationFailureReason.AUTH_FAILURE.value
            elif "429" in err_l or "quota" in err_l:
                fail_reason = VerificationFailureReason.PROVIDER_FAILURE.value
            else:
                fail_reason = VerificationFailureReason.TASK_FAILURE.value

        return TaskExecutionResult(
            execution_id=f"exec_{int(time.time()*1000)}",
            task_id=req.task_id,
            agent_id=self.id,
            provider_id=req.provider_id,
            adapter=self.__class__.__name__,
            command_redacted=redact_secrets(" ".join(cmd)),
            working_directory=str(ws),
            started_at=t0_str,
            ended_at=t1_str,
            duration_ms=dur,
            pid=pid,
            exit_code=code,
            status=status_str,
            failure_reason=fail_reason,
            stdout=stdout,
            stderr=stderr,
            artifacts=new_artifacts,
            capabilities_used=req.required_capabilities
        )

    def stream(self, req: TaskExecutionRequest) -> Iterator[str]:
        """Streams output chunks in real time if supported; falls back to buffered execution."""
        res = self.execute(req)
        if res.stdout:
            yield res.stdout
        if res.stderr:
            yield f"\n[STDERR] {res.stderr}"

    def cancel(self, pid: int) -> bool:
        """Kills the active process tree."""
        return kill_process_tree(pid)

    def health(self, exe_path: str) -> Dict[str, Any]:
        """Quick health ping measuring latency in ms."""
        ok, ver, ev = self.get_version(exe_path)
        return {
            "available": ok,
            "version": ver,
            "version_exit_code": ev.exit_code,
            "latency_ms": ev.duration_ms,
            "timestamp": ev.timestamp
        }

    def diagnostics(self, exe_path: str) -> Dict[str, Any]:
        """Detailed runtime diagnostic report."""
        h = self.health(exe_path)
        auth_st, auth_data = self.check_auth(exe_path)
        providers = self.get_providers(exe_path)
        return {
            "health": h,
            "auth": {"status": auth_st, **auth_data},
            "providers": [p.dict() for p in providers],
            "execution_profile": self.get_execution_profile().dict(),
            "conpty_supported": check_conpty_support()
        }

    def to_model(self, existing: Optional[Dict[str, Any]] = None, probe_ttl_seconds: int = 86400) -> AgentModel:
        """Converts this adapter and its host state into an AgentModel."""
        exe_path = self.discover()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        roles = []
        if existing and "roles" in existing and existing["roles"]:
            roles = existing["roles"]
        else:
            roles = list(self.default_roles)

        if not exe_path:
            return AgentModel(
                id=self.id,
                name=self.name,
                command=self.command,
                provider=self.provider,
                status=AgentStatus.NOT_INSTALLED,
                last_checked=now,
                roles=roles,
                capabilities={cap: CapabilityStatus.UNSUPPORTED.value for cap in ["chat", "code", "file_read", "file_write", "shell", "streaming", "cancellation"]}
            )

        # Run version check to prove availability
        ok, version, ev = self.get_version(exe_path)
        status = AgentStatus.AVAILABLE if ok else AgentStatus.FAILED
        err = None if ok else f"Version check returned code {ev.exit_code}: {ev.stderr or ev.stdout}"

        # Probe auth
        auth_status, auth_data = self.check_auth(exe_path)
        if ok and auth_status in ["AUTHENTICATED", "READY"]:
            status = AgentStatus.READY

        # Discover configured providers
        configured_providers = self.get_providers(exe_path)
        active_provider = None

        # Inherit previous operational evidence if valid
        op_evidence = None
        last_verified = None
        verification_age_seconds = None
        exe_identity = None
        config_fp = None
        cap_evidences = {}

        if existing and existing.get("operational_evidence"):
            try:
                op_evidence = OperationalTestEvidence(**existing["operational_evidence"])
                exe_identity = op_evidence.executable_identity
                config_fp = op_evidence.configuration_fingerprint
                cap_evidences = op_evidence.capability_evidences

                if op_evidence.success:
                    status = AgentStatus.OPERATIONAL
                    last_verified = op_evidence.timestamp
                    if op_evidence.provider_id:
                        active_provider = op_evidence.provider_id

                    # 1. Executable Identity Integrity Gate
                    if exe_identity:
                        valid_exe, exe_reason = is_executable_identity_valid(exe_identity, exe_path)
                        if not valid_exe:
                            status = AgentStatus.STALE
                            err = f"Stale operational verification: {exe_reason} Re-verification required."

                    # 2. Configuration Fingerprint Integrity Gate
                    if status == AgentStatus.OPERATIONAL and config_fp:
                        prof = self.get_execution_profile()
                        curr_caps = [c for c, st in self.get_capabilities(exe_path, operational=True).items() if st == CapabilityStatus.VERIFIED.value]
                        curr_fp = compute_config_fingerprint(
                            exe_identity,
                            version if ok else None,
                            active_provider or self.provider,
                            op_evidence.model,
                            prof.mode.value,
                            curr_caps
                        )
                        if curr_fp != config_fp:
                            status = AgentStatus.STALE
                            err = "Stale operational verification: Configuration fingerprint mismatch. Re-verification required."

                    # 3. Probe TTL Staleness Gate
                    try:
                        t_ver = time.mktime(time.strptime(last_verified, "%Y-%m-%dT%H:%M:%SZ"))
                        verification_age_seconds = max(0, int(time.time() - t_ver))
                        if verification_age_seconds > probe_ttl_seconds:
                            status = AgentStatus.STALE
                            err = f"Operational verification expired ({verification_age_seconds}s > TTL {probe_ttl_seconds}s). Re-verification required."
                    except Exception:
                        pass
            except Exception:
                pass

        if not active_provider and configured_providers:
            active_provider = configured_providers[0].provider

        caps = self.get_capabilities(exe_path, operational=(status == AgentStatus.OPERATIONAL))
        provider_diag = existing.get("provider_diagnostics") if existing else None

        return AgentModel(
            id=self.id,
            name=self.name,
            command=self.command,
            path=exe_path,
            version=version if ok else None,
            provider=self.provider,
            status=status,
            last_checked=now,
            last_verified=last_verified,
            verification_age_seconds=verification_age_seconds,
            capabilities=caps,
            capability_evidences=cap_evidences if status == AgentStatus.OPERATIONAL else {},
            health={"available": ok, "version_exit_code": ev.exit_code, "latency_ms": ev.duration_ms},
            authentication={"status": auth_status, **auth_data},
            execution={"supported": True, "isolated_probe_workspace": True},
            execution_profile=self.get_execution_profile(),
            limits={"default_timeout_seconds": 600},
            error=err or (op_evidence.error if op_evidence and not op_evidence.success else None),
            roles=roles,
            version_evidence=ev,
            operational_evidence=op_evidence,
            executable_identity=exe_identity,
            configuration_fingerprint=config_fp,
            provider_diagnostics=provider_diag,
            configured_providers=configured_providers,
            active_provider=active_provider
        )
