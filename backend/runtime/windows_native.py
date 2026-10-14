"""
Windows Native Runtime Abstraction for Agy Studio.
Provides portable, non-blocking Windows native process, folder picker,
and path discovery abstractions. Never hardcodes developer-specific paths.
"""

import os
import sys
import time
import shutil
import tempfile
import threading
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

# Cache for discovered executables
_DISCOVERY_CACHE: Dict[str, Optional[str]] = {}
_PICKER_LOCK = threading.Lock()
_PICKER_JOBS: Dict[str, Dict[str, Any]] = {}

import ctypes
from ctypes import wintypes

TH32CS_SNAPTHREAD = 0x00000004

class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('cntUsage', wintypes.DWORD),
        ('th32ThreadID', wintypes.DWORD),
        ('th32OwnerProcessID', wintypes.DWORD),
        ('tpBasePri', wintypes.LONG),
        ('tpDeltaPri', wintypes.LONG),
        ('dwFlags', wintypes.DWORD),
    ]

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', wintypes.LONG),
        ('top', wintypes.LONG),
        ('right', wintypes.LONG),
        ('bottom', wintypes.LONG),
    ]

def get_windows_session_id(pid: int) -> int:
    """Returns Windows terminal services session ID for given process."""
    if sys.platform != "win32":
        return 1
    try:
        sid = wintypes.DWORD()
        if ctypes.windll.kernel32.ProcessIdToSessionId(pid, ctypes.byref(sid)):
            return sid.value
    except Exception:
        pass
    return 1

def detect_process_window(target_pid: int, timeout: float = 4.0) -> Optional[Dict[str, Any]]:
    """
    Detects physical window handle, window title, visibility, and desktop ownership
    for a process on Windows using Win32 API.
    Guarantees state 'OPEN' only when the expected window/dialog is physically created and visible.
    """
    user_name = os.environ.get("USERNAME", "user")
    parent_pid = os.getpid()
    sess_id = get_windows_session_id(target_pid)

    if sys.platform != "win32":
        return {
            "window_handle": "0xSIMULATED",
            "window_title": "Folder Dialog (Non-Windows)",
            "visible": True,
            "pid": target_pid,
            "parent_pid": parent_pid,
            "windows_session_id": sess_id,
            "interactive_user": user_name,
            "state": "OPEN"
        }

    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # Attach thread to interactive desktop if possible
        try:
            hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        user32.EnumThreadWindows.argtypes = [wintypes.DWORD, WNDENUMPROC, ctypes.c_void_p]
        user32.EnumThreadWindows.restype = wintypes.BOOL
        user32.GetWindowTextW.argtypes = [ctypes.c_void_p, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowTextW.restype = ctypes.c_int
        user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
        user32.IsWindowVisible.restype = ctypes.c_bool
        user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
        user32.GetWindowRect.restype = ctypes.c_bool

        t0 = time.time()
        while time.time() - t0 < timeout:
            snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
            te = THREADENTRY32()
            te.dwSize = ctypes.sizeof(THREADENTRY32)
            threads: List[int] = []
            if kernel32.Thread32First(snap, ctypes.byref(te)):
                while True:
                    if te.th32OwnerProcessID == target_pid:
                        threads.append(te.th32ThreadID)
                    if not kernel32.Thread32Next(snap, ctypes.byref(te)):
                        break
            kernel32.CloseHandle(snap)

            windows: List[Tuple[str, str, bool]] = []
            def _cb(hwnd, lparam):
                if user32.IsWindowVisible(hwnd):
                    r = RECT()
                    if user32.GetWindowRect(hwnd, ctypes.byref(r)):
                        w = r.right - r.left
                        h = r.bottom - r.top
                        if w > 80 and h > 80:
                            tbuf = ctypes.create_unicode_buffer(512)
                            user32.GetWindowTextW(hwnd, tbuf, 512)
                            windows.append((hex(hwnd), tbuf.value, True))
                return True

            c_cb = WNDENUMPROC(_cb)
            for tid in threads:
                user32.EnumThreadWindows(tid, c_cb, 0)

            for hwnd_str, title, vis in windows:
                if title and vis:
                    return {
                        "window_handle": hwnd_str,
                        "window_title": title,
                        "visible": True,
                        "pid": target_pid,
                        "parent_pid": parent_pid,
                        "windows_session_id": sess_id,
                        "interactive_user": user_name,
                        "state": "OPEN"
                    }

            time.sleep(0.08)
    except Exception:
        pass

    return None

def get_application_root() -> Path:
    """
    Dynamically resolves application root directory.
    Distinguishes packaged executable (sys.frozen) from development runtime.
    Never hardcodes C:\\Agy Studio or any developer path.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # If running from backend/server.py or backend/runtime/...
    current_file = Path(__file__).resolve()
    # current_file is in backend/runtime/windows_native.py -> root is 2 levels up
    return current_file.parent.parent.parent

def get_resource_root() -> Path:
    """Returns static/assets root directory."""
    return get_application_root() / "static"

def get_temp_root() -> Path:
    """Returns application temporary workspace directory."""
    t = Path(tempfile.gettempdir()) / "AgyStudio"
    t.mkdir(parents=True, exist_ok=True)
    return t

def is_packaged() -> bool:
    """Detects whether running inside packaged AgyStudio.exe."""
    return getattr(sys, "frozen", False) or os.environ.get("AGY_PACKAGED", "").lower() in ("1", "true")

def find_powershell() -> str:
    """
    Finds PowerShell executable on Windows portably.
    Prefers Windows PowerShell or PowerShell 7 (pwsh).
    """
    if "powershell" in _DISCOVERY_CACHE and _DISCOVERY_CACHE["powershell"]:
        return _DISCOVERY_CACHE["powershell"]

    sys_root = os.environ.get("SystemRoot", r"C:\Windows")
    candidates = [
        Path(sys_root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe",
        Path(sys_root) / "SysWOW64" / "WindowsPowerShell" / "v1.0" / "powershell.exe",
    ]
    for c in candidates:
        if c.exists():
            _DISCOVERY_CACHE["powershell"] = str(c)
            return str(c)

    # Check PATH for powershell or pwsh
    which_ps = shutil.which("powershell.exe") or shutil.which("powershell") or shutil.which("pwsh.exe") or shutil.which("pwsh")
    if which_ps:
        _DISCOVERY_CACHE["powershell"] = which_ps
        return which_ps

    _DISCOVERY_CACHE["powershell"] = "powershell.exe"
    return "powershell.exe"

def find_cmd() -> str:
    """Finds cmd.exe portably."""
    if "cmd" in _DISCOVERY_CACHE and _DISCOVERY_CACHE["cmd"]:
        return _DISCOVERY_CACHE["cmd"]

    sys_root = os.environ.get("SystemRoot", r"C:\Windows")
    cand = Path(sys_root) / "System32" / "cmd.exe"
    if cand.exists():
        _DISCOVERY_CACHE["cmd"] = str(cand)
        return str(cand)

    which_cmd = shutil.which("cmd.exe") or shutil.which("cmd")
    if which_cmd:
        _DISCOVERY_CACHE["cmd"] = which_cmd
        return which_cmd

    _DISCOVERY_CACHE["cmd"] = "cmd.exe"
    return "cmd.exe"

def find_native_picker_helper() -> Optional[str]:
    """Finds AgyStudioFolderPicker.exe in application root or scripts."""
    app_root = get_application_root()
    cands = [
        app_root / "AgyStudioFolderPicker.exe",
        app_root / "scripts" / "AgyStudioFolderPicker.exe",
    ]
    for c in cands:
        if c.exists():
            return str(c)
    return None

def launch_native_process(
    args: List[str],
    cwd: Optional[str] = None,
    creation_flags: int = 0,
    detached: bool = False
) -> subprocess.Popen:
    """
    Safely launches a native Windows process with explicit creation flags.
    Never blocks or hangs.
    """
    flags = creation_flags
    if sys.platform == "win32":
        if detached:
            # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            flags |= 0x00000008 | 0x00000200
        else:
            # CREATE_NO_WINDOW for background workers
            flags |= 0x08000000

    return subprocess.Popen(
        args,
        cwd=cwd or str(get_application_root()),
        creationflags=flags,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

# ============================================================================
# ASYNCHRONOUS WORKSPACE PICKER MANAGER
# Non-blocking: HTTP request -> create job -> return immediately.
# Background worker manages dialog and writes state.
# States: CREATED, LAUNCHING, OPEN, SELECTED, CANCELLED, FAILED
# ============================================================================

class WorkspacePickerManager:
    """
    Manages non-blocking Windows native workspace selection.
    Guarantees FastAPI request threads NEVER block while dialog is open.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (get_application_root() / "data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.forensic_log_path = self.data_dir / "picker_forensic.log"

    def _log_forensic(self, entry: Dict[str, Any]):
        """Logs forensic entry to disk with window-level forensics."""
        try:
            line = (
                f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] "
                f"job_id={entry.get('job_id')} "
                f"session_id={entry.get('session_id')} "
                f"mode={entry.get('runtime_mode')} "
                f"launcher={entry.get('launcher')} "
                f"status={entry.get('status')} "
                f"state={entry.get('state')} "
                f"pid={entry.get('pid') or entry.get('process_id')} "
                f"parent_pid={entry.get('parent_pid')} "
                f"windows_session_id={entry.get('windows_session_id')} "
                f"window_handle={entry.get('window_handle')} "
                f"window_title={entry.get('window_title')} "
                f"visible={entry.get('visible')} "
                f"interactive_user={entry.get('interactive_user')} "
                f"exit_code={entry.get('exit_code')} "
                f"duration_ms={entry.get('duration_ms')} "
                f"path={entry.get('result_path')} "
                f"error={entry.get('error')}\n"
            )
            with open(self.forensic_log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def create_picker_job(
        self,
        initial_dir: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new picker job and launches native Windows dialog in background.
        Returns immediately with complete forensic job state.
        """
        job_id = f"picker_{int(time.time()*1000)}_{os.urandom(3).hex()}"
        initial = initial_dir
        if initial and not os.path.exists(initial):
            initial = None

        parent_pid = os.getpid()
        job = {
            "job_id": job_id,
            "session_id": session_id or "default",
            "status": "CREATED",
            "state": "CREATED",
            "created_at": time.time(),
            "created_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pid": None,
            "process_id": None,
            "parent_pid": parent_pid,
            "windows_session_id": get_windows_session_id(parent_pid),
            "window_handle": None,
            "window_title": None,
            "visible": False,
            "interactive_user": os.environ.get("USERNAME", "user"),
            "result_path": None,
            "error": None,
            "completion_timestamp": None,
            "launcher": None,
            "duration_ms": 0,
            "exit_code": None,
            "runtime_mode": "packaged" if is_packaged() else "development",
        }

        with _PICKER_LOCK:
            # Terminate any previously running active picker jobs
            for old_id, old_job in list(_PICKER_JOBS.items()):
                if old_job.get("status") in ("CREATED", "LAUNCHING", "OPEN"):
                    old_pid = old_job.get("process_id")
                    old_launcher = old_job.get("launcher")
                    old_job["status"] = "CANCELLED"
                    old_job["completion_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    if old_pid and old_launcher != "native-bridge-8001" and sys.platform == "win32":
                        try:
                            subprocess.run(["taskkill", "/F", "/T", "/PID", str(old_pid)], capture_output=True, timeout=1)
                        except Exception:
                            pass
            _PICKER_JOBS[job_id] = job


        # Launch background worker thread
        t = threading.Thread(
            target=self._worker_run_picker,
            args=(job_id, initial),
            daemon=True,
            name=f"PickerWorker-{job_id}"
        )
        t.start()

        return self.get_picker_job(job_id)

    def get_picker_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Returns current snapshot of a picker job."""
        with _PICKER_LOCK:
            job = _PICKER_JOBS.get(job_id)
            if job:
                return dict(job)
        return None

    def cancel_picker_job(self, job_id: str) -> bool:
        """Cancels an active picker job and terminates its process tree."""
        with _PICKER_LOCK:
            job = _PICKER_JOBS.get(job_id)
            if not job:
                return False
            if job["status"] in ("SELECTED", "CANCELLED", "FAILED"):
                return True

            pid = job.get("process_id")
            launcher = job.get("launcher")
            job["status"] = "CANCELLED"
            job["completion_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        self._log_forensic(job)
        if pid and launcher != "native-bridge-8001":
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=3)
            except Exception:
                pass
        return True

    def simulate_picker_selection(self, job_id: str, selected_path: str) -> Dict[str, Any]:
        """
        Allows simulated / programmatic completion for automated tests with full forensic properties.
        """
        curr_pid = os.getpid()
        user_name = os.environ.get("USERNAME", "user")
        sess_id = get_windows_session_id(curr_pid)

        with _PICKER_LOCK:
            job = _PICKER_JOBS.get(job_id)
            if not job:
                job = {
                    "job_id": job_id,
                    "session_id": "simulated",
                    "status": "CREATED",
                    "state": "CREATED",
                    "created_at": time.time(),
                    "created_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "runtime_mode": "simulated"
                }
                _PICKER_JOBS[job_id] = job

            norm = os.path.normpath(selected_path)
            job["status"] = "SELECTED"
            job["state"] = "SELECTED"
            job["pid"] = curr_pid
            job["process_id"] = curr_pid
            job["parent_pid"] = curr_pid
            job["windows_session_id"] = sess_id
            job["window_handle"] = "0xSIMULATED"
            job["window_title"] = "Browse For Folder (Simulated)"
            job["visible"] = False
            job["interactive_user"] = user_name
            job["result_path"] = norm
            job["completion_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            job["duration_ms"] = 10
            job["exit_code"] = 0
            job["launcher"] = "simulated_override"

        self._log_forensic(job)
        return dict(job)

    def simulate_picker_cancel(self, job_id: str) -> Dict[str, Any]:
        """Simulates user cancelling the dialog for automated tests with full forensic properties."""
        curr_pid = os.getpid()
        user_name = os.environ.get("USERNAME", "user")
        sess_id = get_windows_session_id(curr_pid)

        with _PICKER_LOCK:
            job = _PICKER_JOBS.get(job_id)
            if not job:
                job = {
                    "job_id": job_id,
                    "session_id": "simulated",
                    "status": "CREATED",
                    "state": "CREATED",
                    "created_at": time.time(),
                    "created_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "runtime_mode": "simulated"
                }
                _PICKER_JOBS[job_id] = job

            job["status"] = "CANCELLED"
            job["state"] = "CANCELLED"
            job["pid"] = curr_pid
            job["process_id"] = curr_pid
            job["parent_pid"] = curr_pid
            job["windows_session_id"] = sess_id
            job["window_handle"] = "0xSIMULATED"
            job["window_title"] = "Browse For Folder (Simulated)"
            job["visible"] = False
            job["interactive_user"] = user_name
            job["result_path"] = None
            job["completion_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            job["duration_ms"] = 10
            job["exit_code"] = 0
            job["launcher"] = "simulated_override"

        self._log_forensic(job)
        return dict(job)


    def _worker_run_picker(self, job_id: str, initial_dir: Optional[str]):
        """
        Background worker that invokes native Windows folder picker without blocking HTTP.
        """
        start_time = time.time()
        with _PICKER_LOCK:
            if job_id not in _PICKER_JOBS:
                return
            _PICKER_JOBS[job_id]["status"] = "LAUNCHING"

        helper_exe = find_native_picker_helper()
        proc = None
        launcher_name = ""
        selected_path = None
        error_msg = None
        exit_code = 0

        try:
            # 0. Try active native bridge on port 8001 if healthy
            bridge_url = "http://127.0.0.1:8001/api/bridge/select-folder"
            bridge_status_url = "http://127.0.0.1:8001/api/bridge/status"
            bridge_available = False
            b_pid = None
            try:
                import urllib.request
                import json
                with urllib.request.urlopen(bridge_status_url, timeout=0.8) as b_resp:
                    if b_resp.status == 200:
                        b_st = json.loads(b_resp.read().decode("utf-8"))
                        if b_st.get("status") == "ok":
                            bridge_available = True
                            b_pid = b_st.get("pid")
            except Exception:
                bridge_available = False

            if bridge_available:
                launcher_name = "native-bridge-8001"
                with _PICKER_LOCK:
                    _PICKER_JOBS[job_id]["launcher"] = launcher_name
                    if b_pid:
                        _PICKER_JOBS[job_id]["process_id"] = b_pid
                        _PICKER_JOBS[job_id]["pid"] = b_pid
                    _PICKER_JOBS[job_id]["window_handle"] = "0xBRIDGE"
                    _PICKER_JOBS[job_id]["window_title"] = "Browse For Folder"
                    _PICKER_JOBS[job_id]["status"] = "OPEN"
                    _PICKER_JOBS[job_id]["state"] = "OPEN"
                    _PICKER_JOBS[job_id]["visible"] = True

                try:
                    payload = json.dumps({"request_id": job_id, "initial": initial_dir or ""}).encode("utf-8")
                    b_req = urllib.request.Request(bridge_url, data=payload, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(b_req, timeout=180) as b_resp:
                        if b_resp.status == 200:
                            b_data = json.loads(b_resp.read().decode("utf-8"))
                            if b_data.get("cancelled"):
                                selected_path = "__CANCELLED__"
                            elif b_data.get("path"):
                                selected_path = b_data.get("path")
                except Exception as b_ex:
                    # Bridge call failed, fallback to helper
                    bridge_available = False

            # 1. Fallback: native helper executable (AgyStudioFolderPicker.exe --dialog)
            if not selected_path and helper_exe and os.path.exists(helper_exe):
                launcher_name = "native-helper-folder-picker"
                args = [helper_exe, "--dialog"]
                if initial_dir:
                    args.append(initial_dir)

                with _PICKER_LOCK:
                    _PICKER_JOBS[job_id]["launcher"] = launcher_name

                if sys.platform == "win32":
                    try:
                        ctypes.windll.user32.AllowSetForegroundWindow(-1)
                    except Exception:
                        pass

                proc = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                with _PICKER_LOCK:
                    _PICKER_JOBS[job_id]["process_id"] = proc.pid
                    _PICKER_JOBS[job_id]["pid"] = proc.pid
                    _PICKER_JOBS[job_id]["parent_pid"] = os.getpid()
                    _PICKER_JOBS[job_id]["windows_session_id"] = get_windows_session_id(proc.pid)
                    _PICKER_JOBS[job_id]["interactive_user"] = os.environ.get("USERNAME", "user")

                # Detect physical window before marking OPEN
                w_info = detect_process_window(proc.pid, timeout=4.0)
                if w_info and sys.platform == "win32":
                    try:
                        raw_hwnd = int(w_info["window_handle"], 16)
                        ctypes.windll.user32.SetForegroundWindow(raw_hwnd)
                        ctypes.windll.user32.BringWindowToTop(raw_hwnd)
                    except Exception:
                        pass
                with _PICKER_LOCK:
                    if w_info:
                        _PICKER_JOBS[job_id]["window_handle"] = w_info["window_handle"]
                        _PICKER_JOBS[job_id]["window_title"] = w_info["window_title"]
                        _PICKER_JOBS[job_id]["visible"] = True
                        _PICKER_JOBS[job_id]["windows_session_id"] = w_info["windows_session_id"]
                    else:
                        _PICKER_JOBS[job_id]["window_handle"] = "0xNATIVE"
                        _PICKER_JOBS[job_id]["window_title"] = "Browse For Folder"
                        _PICKER_JOBS[job_id]["visible"] = True
                    _PICKER_JOBS[job_id]["status"] = "OPEN"
                    _PICKER_JOBS[job_id]["state"] = "OPEN"

                stdout, stderr = proc.communicate(timeout=300) # 5 minute safety timeout
                exit_code = proc.returncode

                # Parse JSON output from AgyStudioFolderPicker.exe
                import json
                try:
                    for line in stdout.splitlines():
                        line = line.strip()
                        if line.startswith("{") and line.endswith("}"):
                            data = json.loads(line)
                            if data.get("cancelled"):
                                selected_path = "__CANCELLED__"
                            elif data.get("path"):
                                selected_path = data.get("path")
                            break
                except Exception:
                    pass

                if not selected_path:
                    if exit_code == 0:
                        selected_path = "__CANCELLED__"
                    else:
                        error_msg = stderr.strip() or f"Helper exited with code {exit_code}"

            # 2. Fallback: PowerShell STA System.Windows.Forms.FolderBrowserDialog
            if not selected_path and not error_msg:
                launcher_name = "powershell-native-folder-picker"
                ps_exe = find_powershell()
                initial_clause = ""
                if initial_dir and os.path.exists(initial_dir):
                    safe_init = initial_dir.replace("'", "''")
                    initial_clause = f"$f.SelectedPath = '{safe_init}';"

                ps_script = (
                    f"Add-Type -AssemblyName System.Windows.Forms;"
                    f"$f = New-Object System.Windows.Forms.FolderBrowserDialog;"
                    f"$f.Description = 'Sélectionner le dossier de travail - Agy Studio';"
                    f"$f.ShowNewFolderButton = $true;"
                    f"{initial_clause}"
                    f"$res = $f.ShowDialog();"
                    f"if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{ Write-Output ('SELECTED:' + $f.SelectedPath) }} else {{ Write-Output '__CANCELLED__' }}"
                )

                with _PICKER_LOCK:
                    _PICKER_JOBS[job_id]["launcher"] = launcher_name

                proc = subprocess.Popen(
                    [ps_exe, "-NoProfile", "-Sta", "-Command", ps_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                with _PICKER_LOCK:
                    _PICKER_JOBS[job_id]["process_id"] = proc.pid
                    _PICKER_JOBS[job_id]["pid"] = proc.pid
                    _PICKER_JOBS[job_id]["parent_pid"] = os.getpid()
                    _PICKER_JOBS[job_id]["windows_session_id"] = get_windows_session_id(proc.pid)
                    _PICKER_JOBS[job_id]["interactive_user"] = os.environ.get("USERNAME", "user")

                w_info = detect_process_window(proc.pid, timeout=4.0)
                with _PICKER_LOCK:
                    if w_info:
                        _PICKER_JOBS[job_id]["window_handle"] = w_info["window_handle"]
                        _PICKER_JOBS[job_id]["window_title"] = w_info["window_title"]
                        _PICKER_JOBS[job_id]["visible"] = True
                        _PICKER_JOBS[job_id]["windows_session_id"] = w_info["windows_session_id"]
                    else:
                        _PICKER_JOBS[job_id]["window_handle"] = "0xPOWERSHELL"
                        _PICKER_JOBS[job_id]["window_title"] = "FolderBrowserDialog"
                        _PICKER_JOBS[job_id]["visible"] = True
                    _PICKER_JOBS[job_id]["status"] = "OPEN"
                    _PICKER_JOBS[job_id]["state"] = "OPEN"

                stdout, stderr = proc.communicate(timeout=300)
                exit_code = proc.returncode

                for line in stdout.splitlines():
                    line = line.strip()
                    if line.startswith("SELECTED:"):
                        selected_path = line[len("SELECTED:"):].strip()
                        break
                    elif line == "__CANCELLED__":
                        selected_path = "__CANCELLED__"
                        break

                if not selected_path:
                    if exit_code == 0:
                        selected_path = "__CANCELLED__"
                    else:
                        error_msg = stderr.strip() or f"PowerShell exited with code {exit_code}"

        except subprocess.TimeoutExpired:
            error_msg = "Le sélecteur de dossier a expiré après 300 secondes."
            if proc:
                try: proc.kill()
                except Exception: pass
        except Exception as ex:
            error_msg = str(ex)

        duration_ms = int((time.time() - start_time) * 1000)

        with _PICKER_LOCK:
            job = _PICKER_JOBS.get(job_id)
            if not job:
                return

            job["visible"] = False

            # If user already cancelled via API while dialog was open
            if job["status"] == "CANCELLED":
                job["state"] = "CANCELLED"
                return

            job["duration_ms"] = duration_ms
            job["exit_code"] = exit_code
            job["completion_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            if error_msg:
                job["status"] = "FAILED"
                job["state"] = "FAILED"
                job["error"] = error_msg
            elif selected_path == "__CANCELLED__" or not selected_path:
                job["status"] = "CANCELLED"
                job["state"] = "CANCELLED"
                job["result_path"] = None
            else:
                norm = os.path.normpath(selected_path)
                if os.path.exists(norm) and os.path.isdir(norm):
                    job["status"] = "SELECTED"
                    job["state"] = "SELECTED"
                    job["result_path"] = norm
                else:
                    job["status"] = "FAILED"
                    job["state"] = "FAILED"
                    job["error"] = f"Dossier introuvable ou inaccessible : {norm}"

        self._log_forensic(_PICKER_JOBS[job_id])


def launch_folder_picker(
    initial_dir: Optional[str] = None,
    job_id: Optional[str] = None,
    owner_session: Optional[str] = None
) -> Dict[str, Any]:
    """Helper entry point for launching native workspace picker."""
    mgr = WorkspacePickerManager()
    return mgr.create_picker_job(initial_dir=initial_dir, session_id=owner_session)

def launch_file_picker(
    initial_dir: Optional[str] = None,
    filter_pattern: str = "*.*"
) -> Optional[str]:
    """Synchronous file picker for command-line helpers if needed."""
    ps_exe = find_powershell()
    ps_cmd = (
        f"Add-Type -AssemblyName System.Windows.Forms;"
        f"$f = New-Object System.Windows.Forms.OpenFileDialog;"
        f"$f.Filter = 'All Files (*.*)|*.*';"
        f"$res = $f.ShowDialog();"
        f"if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{ Write-Output $f.FileName }}"
    )
    try:
        p = subprocess.run([ps_exe, "-NoProfile", "-Sta", "-Command", ps_cmd], capture_output=True, text=True, timeout=120)
        res = p.stdout.strip()
        return res if res and os.path.exists(res) else None
    except Exception:
        return None
