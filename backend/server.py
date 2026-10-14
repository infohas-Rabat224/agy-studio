import os
import sys
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parent.parent
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))
if str(STUDIO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT / "backend"))

import json
import time
import shutil
import glob
import re
import logging
import urllib.parse
import subprocess
from typing import Optional, List, Dict, Any, Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel

try:
    from backend.mcp import mcp_manager, MCPServerConfig, MCPToolCallRequest
except ImportError:
    try:
        from mcp import mcp_manager, MCPServerConfig, MCPToolCallRequest
    except Exception as _mcp_err:
        mcp_manager = None
        MCPServerConfig = None
        MCPToolCallRequest = None

app = FastAPI(title="Agy Studio Agentic API", version="2.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STUDIO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = STUDIO_ROOT / "data"
MEDIA_DIR = DATA_DIR / "media"
CONFIG_FILE = DATA_DIR / "config.json"
MEMORY_FILE = DATA_DIR / "memory.json"
DEFAULT_WORKSPACE = str(Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Documents" / "gemini-projects")
SETTINGS_PATH = Path(os.path.expanduser(r"~/.gemini/antigravity-cli/settings.json"))

app.state.config_file = CONFIG_FILE
app.state.default_workspace = DEFAULT_WORKSPACE

try:
    from backend.advanced_features import advanced_router
except ImportError:
    try:
        from advanced_features import advanced_router
    except Exception as _adv_err:
        advanced_router = None

if advanced_router:
    app.include_router(advanced_router)

_local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))

def _discover_uv() -> str:
    """Discover uv.exe portably without assuming any specific username or install path."""
    candidates = [
        STUDIO_ROOT / "runtime" / "uv.exe",               # Bundled portable runtime
        _local / "hermes" / "bin" / "uv.exe",             # Hermes install
        _local / "uv" / "uv.exe",                         # Standard uv location
        _local / "Programs" / "astral" / "uv" / "uv.exe", # Astral Programs
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    found = shutil.which("uv")
    return found or str(candidates[1])  # keep Hermes as last-resort default display path

def _discover_agy() -> str:
    """Discover agy.EXE portably."""
    candidates = [
        STUDIO_ROOT / "runtime" / "agy.EXE",
        _local / "agy" / "bin" / "agy.EXE",
        _local / "agy" / "bin" / "agy.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    found = shutil.which("agy")
    return found or str(candidates[1])

UV_PATH = _discover_uv()
AGY_EXE = _discover_agy()
SKILLS_DIR = STUDIO_ROOT / "skills"

def ensure_portable_skills_registered(workspace_path: Optional[Path] = None):
    """Ensure portable skills folder is known to agy CLI globally and in workspace."""
    if not SKILLS_DIR.exists():
        return
    # 1. Register in ~/.gemini/config/skills.json
    try:
        user_config_dir = Path.home() / ".gemini" / "config"
        user_config_dir.mkdir(parents=True, exist_ok=True)
        global_skills_cfg = user_config_dir / "skills.json"
        skills_path_str = str(SKILLS_DIR.resolve()).replace("\\", "/")
        entries = []
        if global_skills_cfg.exists():
            try:
                with open(global_skills_cfg, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    entries = data.get("entries", [])
            except Exception:
                entries = []
        already = any(e.get("path") == skills_path_str for e in entries if isinstance(e, dict))
        if not already:
            entries.append({"path": skills_path_str})
            with open(global_skills_cfg, "w", encoding="utf-8") as f:
                json.dump({"entries": entries}, f, indent=2)
            logging.info(f"Registered portable skills globally in {global_skills_cfg}")
    except Exception as e:
        logging.warning(f"Could not register portable skills globally: {e}")

    # 2. Register in active workspace (.agents/skills.json)
    if workspace_path and workspace_path.exists() and workspace_path.is_dir():
        try:
            agents_dir = workspace_path / ".agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            ws_skills_cfg = agents_dir / "skills.json"
            skills_path_str = str(SKILLS_DIR.resolve()).replace("\\", "/")
            ws_entries = []
            if ws_skills_cfg.exists():
                try:
                    with open(ws_skills_cfg, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        ws_entries = data.get("entries", [])
                except Exception:
                    ws_entries = []
            if not any(e.get("path") == skills_path_str for e in ws_entries if isinstance(e, dict)):
                ws_entries.append({"path": skills_path_str})
                with open(ws_skills_cfg, "w", encoding="utf-8") as f:
                    json.dump({"entries": ws_entries}, f, indent=2)
                logging.info(f"Attached portable skills to workspace: {workspace_path}")
        except Exception as e:
            logging.warning(f"Could not attach skills to workspace {workspace_path}: {e}")



DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

for fname, default_val in [("tasks.json", {}), ("executions.json", {}), ("artifacts.json", []), ("messages.json", []), ("swarm.json", {})]:
    fpath = DATA_DIR / fname
    if not fpath.exists():
        with open(fpath, "w") as f:
            json.dump(default_val, f)

# ----------------- UNIVERSAL SUBSYSTEM INITIALIZATION -----------------
from backend.runtime import (
    find_powershell, find_cmd, is_packaged,
    get_application_root, get_resource_root, get_temp_root,
    WorkspacePickerManager
)
from backend.session import (
    SessionManager, SessionState, SessionRecord
)
from backend.artifacts import (
    ArtifactManager, ArtifactSourceType, ArtifactAcquisition,
    ArtifactCapabilityNegotiator
)
from backend.preview import (
    REAL_PREVIEW_ENABLED, PREVIEW_MAX_SIZE, PreviewMode,
    PREVIEW_SUPPORT_MATRIX, PreviewService, preview_service
)
from backend.memory import (
    MemoryManager, MemoryRecord, MemoryScope, MemoryType,
    MemoryPriority, MemoryConfidence, PreflightRequest, PreflightResult,
    GuardCheckRequest, GuardResult, MemoryCreateRequest,
    MemoryConfirmRequest, MemorySupersedeRequest
)

session_manager = SessionManager.get_instance(DATA_DIR)
artifact_manager = ArtifactManager(DATA_DIR)
preview_service = PreviewService(DATA_DIR, artifact_manager)
picker_manager = WorkspacePickerManager(DATA_DIR)
memory_manager = MemoryManager.get_instance(DATA_DIR)

from backend.intelligence import (
    IntelligenceEngine, ConfidenceLevel, IntentAnalyzer, TaskClassifier,
    ExperienceRetriever, PatternEngine, StrategyEngine, RiskEngine,
    PredictionEngine, AgentPerformanceEngine, OutcomeAnalyzer,
    RegressionDetector, KnowledgeEngine, LearningEngine,
    WorkflowOptimizer, PlanningEngine, IntelligenceGuard
)
intelligence_engine = IntelligenceEngine.get_instance(DATA_DIR, memory_mgr=memory_manager, session_mgr=session_manager)

# ----------------- AGENT REGISTRY & UNIVERSAL CLI ORCHESTRATOR -----------------
try:
    from backend.agent_adapters import AgentRegistry, OrchestratorEngine, OrchestratorDecision, VALID_ROLES
except ModuleNotFoundError:
    from agent_adapters import AgentRegistry, OrchestratorEngine, OrchestratorDecision, VALID_ROLES

agent_registry = AgentRegistry(DATA_DIR)
agent_orchestrator = OrchestratorEngine(agent_registry, DATA_DIR)

# ----------------- CONFIG MANAGER -----------------
def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "workspace": DEFAULT_WORKSPACE,
        "authorization_mode": "permanent", # 'permanent', 'temporary', 'ask'
        "temp_auth_until": 0,
        "active_mode": "pedagogie",
        "theme": "dark",
        "model": "gemini-3.8-flash-medium"
    }

def save_config(cfg: Dict[str, Any]):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

current_config = load_config()
try:
    ws_init = Path(current_config.get("workspace", DEFAULT_WORKSPACE))
    ensure_portable_skills_registered(ws_init)
except Exception:
    pass

class ConfigUpdate(BaseModel):
    workspace: Optional[str] = None
    authorization_mode: Optional[str] = None
    temp_auth_duration_minutes: Optional[int] = None
    active_mode: Optional[str] = None
    theme: Optional[str] = None
    model: Optional[str] = None
    language: Optional[str] = None
    hitl_mode: Optional[str] = None

@app.get("/api/config")
def get_config():
    now = time.time()
    is_temp_valid = (
        current_config.get("authorization_mode") == "temporary" 
        and current_config.get("temp_auth_until", 0) > now
    )
    return {
        "workspace": current_config.get("workspace", DEFAULT_WORKSPACE),
        "authorization_mode": current_config.get("authorization_mode", "permanent"),
        "temp_auth_active": is_temp_valid,
        "temp_auth_remaining_seconds": max(0, int(current_config.get("temp_auth_until", 0) - now)) if is_temp_valid else 0,
        "active_mode": current_config.get("active_mode", "pedagogie"),
        "theme": current_config.get("theme", "dark"),
        "model": current_config.get("model", "gemini-3.8-flash-medium"),
        "language": current_config.get("language", "fr"),
        "hitl_mode": current_config.get("hitl_mode", "active"),
        "uv_available": os.path.exists(UV_PATH),
        "agy_available": os.path.exists(AGY_EXE),
        "studio_root": str(STUDIO_ROOT)
    }

@app.post("/api/config")
def update_config(update: ConfigUpdate):
    if update.workspace:
        if not os.path.exists(update.workspace):
            raise HTTPException(status_code=400, detail=f"Dossier introuvable : {update.workspace}")
        current_config["workspace"] = os.path.abspath(update.workspace)
    if update.authorization_mode:
        if update.authorization_mode not in ["permanent", "temporary", "ask"]:
            raise HTTPException(status_code=400, detail="Mode d'autorisation invalide")
        current_config["authorization_mode"] = update.authorization_mode
        if update.authorization_mode == "temporary":
            duration = update.temp_auth_duration_minutes or 60
            current_config["temp_auth_until"] = time.time() + (duration * 60)
        else:
            current_config["temp_auth_until"] = 0
    if update.active_mode:
        current_config["active_mode"] = update.active_mode
    if update.theme:
        current_config["theme"] = update.theme
    if update.model:
        current_config["model"] = update.model
        persist_model_to_settings(update.model)
    if update.language:
        current_config["language"] = update.language.lower()
    if update.hitl_mode:
        current_config["hitl_mode"] = update.hitl_mode.lower()

    save_config(current_config)
    return get_config()

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Startup actions
    try:
        crashed = session_manager.recover_previous_sessions()
        if crashed:
            logging.info(f"Recovered {len(crashed)} previously crashed session(s): {crashed}")
    except Exception as e:
        logging.warning(f"Error during session recovery: {e}")

    try:
        curr_ws = current_config.get("workspace", DEFAULT_WORKSPACE)
        active_sess = session_manager.create_session(workspace=curr_ws)
        session_manager.add_event("SERVER_STARTED", "FastAPI", {"port": 8000, "session_id": active_sess.session_id})
        logging.info(f"Active session started: {active_sess.session_id}")
    except Exception as e:
        logging.warning(f"Error creating startup session: {e}")

    ensure_picker_bridge()
    try:
        agent_registry.discover_all()
    except Exception as e:
        logging.warning(f"Could not run startup agent discovery: {e}")

    yield

    # Shutdown actions
    try:
        session_manager.close_session("normal_application_shutdown")
        logging.info("Active session gracefully closed")
    except Exception as e:
        logging.warning(f"Error closing session on shutdown: {e}")

app.router.lifespan_context = lifespan

# ================= WORKSPACE API =================
@app.get("/api/workspace")
def get_workspace_context():
    raw_ws = current_config.get("workspace", DEFAULT_WORKSPACE)
    norm = os.path.normpath(raw_ws)
    p = Path(norm)
    exists = p.exists()
    is_dir = p.is_dir() if exists else False
    readable = os.access(norm, os.R_OK) if exists else False
    writable = os.access(norm, os.W_OK) if exists else False
    free_space = 0
    if exists and hasattr(shutil, "disk_usage"):
        try:
            free_space = shutil.disk_usage(norm).free
        except Exception:
            pass

    return {
        "workspace_id": f"ws_{hashlib.md5(norm.encode()).hexdigest()[:12]}",
        "path": norm,
        "name": os.path.basename(norm) or norm,
        "exists": exists,
        "is_directory": is_dir,
        "readable": readable,
        "writable": writable,
        "free_space_bytes": free_space
    }

class WorkspacePickerRequest(BaseModel):
    initial: Optional[str] = None
    session_id: Optional[str] = None

@app.post("/api/workspace/picker")
def post_workspace_picker(req: Optional[WorkspacePickerRequest] = None):
    initial = (req.initial if req else None) or current_config.get("workspace", DEFAULT_WORKSPACE)
    sess_id = (req.session_id if req else None) or (session_manager.get_current_session().session_id if session_manager.get_current_session() else "default")
    job = picker_manager.create_picker_job(initial_dir=initial, session_id=sess_id)
    return job

@app.get("/api/workspace/picker/{job_id}")
def get_workspace_picker_status(job_id: str):
    job = picker_manager.get_picker_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Picker job introuvable")

    if job.get("status") == "SELECTED" and job.get("result_path"):
        selected = job["result_path"]
        if os.path.exists(selected) and os.path.isdir(selected):
            current_config["workspace"] = selected
            save_config(current_config)
            session_manager.set_session_workspace(selected)

    return job

@app.post("/api/workspace/picker/{job_id}/cancel")
def cancel_workspace_picker(job_id: str):
    ok = picker_manager.cancel_picker_job(job_id)
    return {"status": "ok" if ok else "not_found"}

class WorkspaceSetRequest(BaseModel):
    workspace: Optional[str] = None
    path: Optional[str] = None

@app.post("/api/workspace/set")
def set_workspace_path(req: WorkspaceSetRequest):
    raw = (req.workspace or req.path or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Chemin du workspace manquant")
    norm = os.path.normpath(raw)
    if not os.path.exists(norm) or not os.path.isdir(norm):
        raise HTTPException(status_code=400, detail=f"Dossier introuvable ou invalide : {raw}")
    current_config["workspace"] = norm
    save_config(current_config)
    session_manager.set_session_workspace(norm)
    ensure_portable_skills_registered(Path(norm))
    logging.info(f"WORKSPACE_SET: {norm}")
    return {
        "status": "ok",
        "workspace": norm,
        "name": os.path.basename(norm) or norm,
        "cancelled": False
    }

def check_bridge_health(port: int = 8001) -> Tuple[bool, Dict[str, Any]]:
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/bridge/status")
        with urllib.request.urlopen(req, timeout=0.8) as r:
            if r.status == 200:
                data = json.loads(r.read().decode("utf-8"))
                return True, data
    except Exception:
        pass
    return False, {}

def ensure_picker_bridge(port: int = 8001) -> bool:
    """Ensure AgyStudioFolderPicker.exe native bridge is listening on port 8001."""
    ok, _ = check_bridge_health(port)
    if ok:
        return True

    picker_exe = STUDIO_ROOT / "AgyStudioFolderPicker.exe"
    if picker_exe.exists():
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/f", "/im", "AgyStudioFolderPicker.exe"], capture_output=True)
                time.sleep(0.3)

            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen(
                [str(picker_exe), "--bridge", str(port)],
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
                cwd=str(STUDIO_ROOT)
            )
            logging.info(f"Spawned AgyStudioFolderPicker.exe native bridge on port {port}")
            for _ in range(12):
                time.sleep(0.25)
                if check_bridge_health(port)[0]:
                    return True
        except Exception as e:
            logging.warning(f"Could not spawn AgyStudioFolderPicker bridge: {e}")
    return False

@app.get("/api/bridge/info")
@app.get("/api/bridge/status")
def api_bridge_info():
    port = 8001
    ok, data = check_bridge_health(port)
    if not ok:
        ok = ensure_picker_bridge(port)
        if ok:
            _, data = check_bridge_health(port)
    return {
        "status": "ok" if ok else "unavailable",
        "service": "AgyStudioFolderPicker",
        "bridge": "AgyStudioNativeBridge",
        "port": port,
        "endpoint": f"http://127.0.0.1:{port}",
        "interactive": data.get("interactive", True),
        "pid": data.get("pid"),
        "session_id": data.get("session_id")
    }

@app.post("/api/bridge/ensure")
def api_ensure_bridge():
    ok = ensure_picker_bridge()
    return {"status": "ok" if ok else "error", "port": 8001}

@app.post("/api/workspace/browse")
async def browse_workspace_dialog(request: Request):
    """
    Deprecated for interactive UI: Frontend connects directly to native desktop bridge (127.0.0.1:8001).
    Accepts programmatic override if provided in request body/query.
    """
    selected_path = ""
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            if isinstance(body, dict):
                selected_path = (body.get("path") or body.get("workspace") or "").strip()
    except Exception:
        pass
    if not selected_path:
        selected_path = request.query_params.get("path", "").strip()

    if selected_path:
        norm_path = os.path.normpath(selected_path)
        if os.path.exists(norm_path) and os.path.isdir(norm_path):
            current_config["workspace"] = norm_path
            save_config(current_config)
            logging.info(f"WORKSPACE_SELECTED: {norm_path}")
            return {
                "status": "ok",
                "workspace": norm_path,
                "name": os.path.basename(norm_path) or norm_path,
                "cancelled": False
            }

    # Ensure bridge is running in background so browser can call it directly
    ensure_picker_bridge()
    current_ws = current_config.get("workspace", DEFAULT_WORKSPACE)
    return {
        "status": "bridge_ready",
        "workspace": current_ws,
        "name": os.path.basename(current_ws),
        "bridge_port": 8001,
        "message": "Use http://127.0.0.1:8001/api/bridge/select-folder directly from browser"
    }

# ================= SESSION IDENTITY & PERSISTENCE API =================
@app.get("/api/session")
@app.get("/api/session/current")
def get_active_session():
    curr = session_manager.get_current_session()
    if not curr:
        curr = session_manager.create_session(workspace=current_config.get("workspace", DEFAULT_WORKSPACE))
    return curr.to_dict()

@app.get("/api/sessions")
def get_all_sessions(include_archived: bool = True, include_deleted: bool = False):
    return session_manager.list_sessions(include_archived=include_archived, include_deleted=include_deleted)

@app.get("/api/sessions/search")
def search_sessions(q: str = Query("", alias="q"), include_archived: bool = True, include_deleted: bool = False):
    return session_manager.search_sessions(query=q, include_archived=include_archived, include_deleted=include_deleted)

@app.get("/api/sessions/{session_id}")
def get_session_by_id(session_id: str):
    s = session_manager.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return s.to_dict()

@app.get("/api/sessions/{session_id}/lineage")
def get_session_lineage(session_id: str):
    return session_manager.get_session_lineage(session_id)

class RenameSessionRequest(BaseModel):
    display_name: str

@app.post("/api/sessions/{session_id}/rename")
def rename_session(session_id: str, req: RenameSessionRequest):
    ok = session_manager.rename_session(session_id, req.display_name)
    if not ok:
        raise HTTPException(status_code=400, detail="Impossible de renommer la session")
    return {"status": "ok", "session_id": session_id, "display_name": req.display_name}

@app.post("/api/sessions/{session_id}/pin")
def pin_session(session_id: str):
    ok = session_manager.pin_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"status": "ok", "session_id": session_id, "pinned": True}

@app.post("/api/sessions/{session_id}/unpin")
def unpin_session(session_id: str):
    ok = session_manager.unpin_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"status": "ok", "session_id": session_id, "pinned": False}

@app.post("/api/sessions/{session_id}/favorite")
def favorite_session(session_id: str):
    ok = session_manager.favorite_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"status": "ok", "session_id": session_id, "favorite": True}

@app.post("/api/sessions/{session_id}/unfavorite")
def unfavorite_session(session_id: str):
    ok = session_manager.unfavorite_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"status": "ok", "session_id": session_id, "favorite": False}

@app.post("/api/sessions/{session_id}/archive")
def archive_session(session_id: str):
    ok = session_manager.archive_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"status": "ok", "session_id": session_id, "archived": True}

@app.post("/api/sessions/{session_id}/restore")
def restore_session(session_id: str):
    ok = session_manager.restore_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"status": "ok", "session_id": session_id, "restored": True}

@app.post("/api/sessions/{session_id}/resume")
def resume_session(session_id: str):
    try:
        new_sess = session_manager.resume_session(session_id)
        if new_sess.workspace and os.path.exists(new_sess.workspace):
            current_config["workspace"] = new_sess.workspace
            save_config(current_config)
            ensure_portable_skills_registered(Path(new_sess.workspace))
        return {
            "status": "resumed",
            "new_session": new_sess.to_dict(),
            "source_session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ForkSessionRequest(BaseModel):
    name: Optional[str] = None

@app.post("/api/sessions/{session_id}/fork")
def fork_session(session_id: str, req: Optional[ForkSessionRequest] = None):
    try:
        fork_name = req.name if req else None
        new_sess = session_manager.fork_session(session_id, fork_name=fork_name)
        return {
            "status": "forked",
            "new_session": new_sess.to_dict(),
            "parent_session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sessions/{session_id}/delete")
def delete_session(session_id: str):
    ok = session_manager.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"status": "deleted", "session_id": session_id, "soft_delete": True}

class PermanentDeleteRequest(BaseModel):
    confirm: bool = False

@app.post("/api/sessions/{session_id}/delete-permanently")
def delete_session_permanently(session_id: str, req: Optional[PermanentDeleteRequest] = None):
    if req is not None and not req.confirm:
        raise HTTPException(status_code=400, detail="Confirmation explicite requise pour la suppression définitive.")
    ok, msg = session_manager.delete_permanently(session_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "permanently_deleted", "message": msg}

@app.post("/api/session/close")
def close_session_endpoint():
    ok = session_manager.close_session("user_closed")
    return {"status": "closed" if ok else "error"}

@app.get("/api/session/events")
def get_session_events(session_id: Optional[str] = None):
    s = session_manager.get_session(session_id) if session_id else session_manager.get_current_session()
    if not s:
        return []
    return s.events

@app.get("/api/session/artifacts")
def get_session_artifacts(session_id: Optional[str] = None):
    s = session_manager.get_session(session_id) if session_id else session_manager.get_current_session()
    if not s:
        return []
    return s.artifacts

@app.get("/api/session/executions")
def get_session_executions(session_id: Optional[str] = None):
    s = session_manager.get_session(session_id) if session_id else session_manager.get_current_session()
    if not s:
        return []
    return s.executions

@app.get("/api/session/correlations")
def get_session_correlations(session_id: Optional[str] = None):
    return session_manager.get_correlations(session_id)

@app.get("/api/session/correlations/artifact/{artifact_id}")
def get_correlations_by_artifact(artifact_id: str, session_id: Optional[str] = None):
    return session_manager.find_correlations_by_artifact(artifact_id, session_id)

@app.get("/api/session/correlations/task/{task_id}")
def get_correlations_by_task(task_id: str, session_id: Optional[str] = None):
    return session_manager.find_correlations_by_task(task_id, session_id)

@app.get("/api/session/correlations/execution/{execution_id}")
def get_correlations_by_execution(execution_id: str, session_id: Optional[str] = None):
    return session_manager.find_correlations_by_execution(execution_id, session_id)

# ----------------- MODEL SELECTION & PERSISTENCE -----------------
def persist_model_to_settings(model_id_or_name: str):
    if not SETTINGS_PATH.exists():
        return
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["model"] = model_id_or_name
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error persisting model to settings.json: {e}")

@app.get("/api/models")
def get_models():
    models = []
    if os.path.exists(AGY_EXE):
        try:
            p = subprocess.run([AGY_EXE, "models"], capture_output=True, text=True, timeout=8, encoding="utf-8")
            for line in p.stdout.splitlines():
                if "\t" in line:
                    parts = line.strip().split("\t")
                    models.append({"id": parts[0].strip(), "name": parts[1].strip()})
        except Exception as e:
            print(f"Error listing models: {e}")
    
    if not models:
        models = [
            {"id": "gemini-3.8-flash-high", "name": "Gemini 3.8 Flash (High)"},
            {"id": "gemini-3.8-flash-medium", "name": "Gemini 3.8 Flash (Medium)"},
            {"id": "gemini-3.8-flash-low", "name": "Gemini 3.8 Flash (Low)"},
            {"id": "gemini-3.7-flash-high", "name": "Gemini 3.7 Flash (High)"},
            {"id": "gemini-3.1-pro-high", "name": "Gemini 3.1 Pro (High)"},
            {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6 (Thinking)"},
            {"id": "claude-opus-4-6-thinking", "name": "Claude Opus 4.6 (Thinking)"}
        ]

    curr = current_config.get("model", "gemini-3.8-flash-medium")
    return {
        "current_model": curr,
        "models": models
    }

class SetModelRequest(BaseModel):
    model: str

@app.post("/api/models/set")
def set_model(req: SetModelRequest):
    current_config["model"] = req.model
    save_config(current_config)
    persist_model_to_settings(req.model)
    return {"status": "success", "model": req.model}

# ----------------- LIVE QUOTA STATUS -----------------
@app.get("/api/quota")
def get_live_quota():
    res = {"items": [], "raw": "", "status": "ok"}
    if os.path.exists(AGY_EXE):
        try:
            p = subprocess.run(
                [AGY_EXE, "-p", "/quota", "--dangerously-skip-permissions"],
                capture_output=True,
                text=True,
                timeout=12,
                encoding="utf-8"
            )
            res["raw"] = p.stdout.strip()
            for line in p.stdout.splitlines():
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    m = re.search(r"(\d+)%", parts[2])
                    res["items"].append({
                        "provider": parts[0].strip(),
                        "name": parts[1].strip(),
                        "percent": int(m.group(1)) if m else parts[2].strip(),
                        "reset": parts[3].strip() if len(parts) > 3 else ""
                    })
        except Exception as e:
            res["status"] = "error"
            res["raw"] = f"Erreur quota : {e}"
    return res

# ----------------- LIVE MCP SERVERS & PLUGINS -----------------
class MCPToggleRequest(BaseModel):
    enabled: bool

@app.get("/api/mcp")
def get_mcp_servers():
    if mcp_manager:
        try:
            return mcp_manager.list_servers()
        except Exception as e:
            logging.error(f"Error listing MCP servers: {e}")
    # Fallback to agy CLI if manager failed
    servers = []
    if os.path.exists(AGY_EXE):
        try:
            p = subprocess.run([AGY_EXE, "mcp", "list"], capture_output=True, text=True, timeout=8, encoding="utf-8")
            lines = p.stdout.strip().splitlines()
            for l in lines[1:]:
                parts = re.split(r"\s{2,}", l.strip())
                if len(parts) >= 4:
                    servers.append({
                        "name": parts[0],
                        "type": parts[1],
                        "status": parts[2],
                        "command": parts[3]
                    })
        except Exception as e:
            print("mcp error:", e)

    if not servers:
        servers = [
            {"name": "github", "type": "stdio", "status": "enabled", "command": "npx -y @modelcontextprotocol/server-github"},
            {"name": "system-filesystem", "type": "native", "status": "active", "command": "builtin-antigravity"}
        ]
    return servers

@app.get("/api/mcp/templates")
def get_mcp_templates():
    if mcp_manager:
        return mcp_manager.get_templates()
    return {}

@app.post("/api/mcp/servers")
def save_mcp_server(req: Dict[str, Any]):
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP Manager unavailable")
    try:
        return mcp_manager.add_or_update_server(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/mcp/servers/{name}")
def delete_mcp_server(name: str):
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP Manager unavailable")
    ok = mcp_manager.delete_server(name)
    if not ok:
        raise HTTPException(status_code=404, detail="Server not found")
    return {"success": True, "name": name}

@app.post("/api/mcp/servers/{name}/test")
def test_mcp_server(name: str):
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP Manager unavailable")
    return mcp_manager.test_server(name)

@app.post("/api/mcp/servers/{name}/toggle")
def toggle_mcp_server(name: str, req: MCPToggleRequest):
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP Manager unavailable")
    res = mcp_manager.toggle_server(name, req.enabled)
    if res is None:
        raise HTTPException(status_code=404, detail="Server not found")
    return {"success": True, "server": res}

@app.post("/api/mcp/call")
def call_mcp_tool(req: Dict[str, Any]):
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP Manager unavailable")
    server = req.get("server", "")
    tool = req.get("tool", "")
    arguments = req.get("arguments", {})
    return mcp_manager.call_tool(server, tool, arguments)

@app.get("/api/plugins")
def get_plugins():
    plugins = []
    if os.path.exists(AGY_EXE):
        try:
            p = subprocess.run([AGY_EXE, "plugins", "list"], capture_output=True, text=True, timeout=8, encoding="utf-8")
            return {"raw": p.stdout.strip()}
        except Exception as e:
            return {"raw": str(e)}
    return {"raw": "Plugin manager disponible via agy CLI"}

# ----------------- PERSISTENT LEARNING MEMORY HUB -----------------
@app.get("/api/memory")
def get_memories(
    scope: Optional[str] = None,
    type: Optional[str] = None,
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    active_only: bool = True,
    legacy: bool = False
):
    mems = memory_manager.list_memories(
        scope=scope,
        mem_type=type,
        project_id=project_id,
        session_id=session_id,
        active_only=active_only
    )
    if legacy:
        # Backward compatibility for legacy UI tabs
        cats: Dict[str, List[Any]] = {}
        for m in mems:
            cat = f"Mémoire {m.get('scope', 'GLOBAL')} ({m.get('type', 'GÉNÉRAL')})"
            cats.setdefault(cat, []).append({
                "id": m["memory_id"],
                "title": m["title"],
                "content": m["content"],
                "tag": m["priority"],
                "created_at": m["created_at"]
            })
        return {"version": "2.5.0", "categories": cats, "items": mems}
    return mems

@app.get("/api/memory/search")
def search_memories(q: str = Query("", alias="q"), limit: int = 50):
    return memory_manager.search_memories(query=q, limit=limit)

@app.post("/api/memory")
def create_memory(req: MemoryCreateRequest):
    rec = memory_manager.create_memory(req)
    return rec.to_dict()

@app.post("/api/memory/add")
def add_memory_item_legacy(req: Dict[str, Any]):
    # Adapter for legacy add route
    m_req = MemoryCreateRequest(
        scope="GLOBAL" if "global" in req.get("category", "").lower() else "PROJECT",
        type="CORRECTION" if req.get("tag") == "CRITIQUE" else "LESSON",
        content=req.get("content", ""),
        title=req.get("title"),
        priority="CRITICAL" if req.get("tag") == "CRITIQUE" else "MEDIUM"
    )
    rec = memory_manager.create_memory(m_req)
    return rec.to_dict()

@app.post("/api/memory/{memory_id}/confirm")
def confirm_memory(memory_id: str, req: Optional[MemoryConfirmRequest] = None):
    res = memory_manager.confirm_memory(
        memory_id,
        new_scope=req.scope if req else None,
        new_priority=req.priority if req else None
    )
    if not res:
        raise HTTPException(status_code=404, detail="Mémoire introuvable")
    return res

@app.post("/api/memory/{memory_id}/supersede")
def supersede_memory(memory_id: str, req: MemorySupersedeRequest):
    ok = memory_manager.supersede_memory(memory_id, req.new_memory_id, reason=req.reason or "")
    if not ok:
        raise HTTPException(status_code=404, detail="Mémoire introuvable")
    return {"status": "superseded", "old_id": memory_id, "new_id": req.new_memory_id}

@app.post("/api/memory/{memory_id}/deactivate")
@app.delete("/api/memory/{memory_id}")
def deactivate_memory(memory_id: str):
    ok = memory_manager.deactivate_memory(memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Mémoire introuvable")
    return {"status": "deactivated", "memory_id": memory_id}

@app.post("/api/memory/preflight")
def memory_preflight(req: PreflightRequest):
    ws = req.workspace or current_config.get("workspace", DEFAULT_WORKSPACE)
    curr_sess = session_manager.current_session
    s_id = req.session_id or (curr_sess.session_id if curr_sess else None)
    return memory_manager.preflight_check(
        task=req.task,
        workspace=ws,
        session_id=s_id,
        project_id=req.project_id,
        agent_id=req.agent_id
    )

@app.post("/api/memory/check-guard")
def memory_guard_check(req: GuardCheckRequest):
    ws = req.workspace or current_config.get("workspace", DEFAULT_WORKSPACE)
    curr_sess = session_manager.current_session
    s_id = req.session_id or (curr_sess.session_id if curr_sess else None)
    return memory_manager.check_guard(
        proposal=req.proposal,
        workspace=ws,
        session_id=s_id,
        project_id=req.project_id
    )

# ----------------- ADAPTIVE INTELLIGENCE ENGINE (v2.6) -----------------
class PreflightIntelRequest(BaseModel):
    task: str
    workspace: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None

class IntelExplainRequest(BaseModel):
    topic: str
    identifier: str

class IntelLearnRequest(BaseModel):
    user_text: Optional[str] = None
    rejected_entity: Optional[str] = None
    accepted_alternative: Optional[str] = None
    reason: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None

class IntelSettingsUpdateRequest(BaseModel):
    adaptive_learning: Optional[bool] = None
    automatic_low_risk_learning: Optional[bool] = None
    ask_before_project_wide: Optional[bool] = None
    ask_before_global: Optional[bool] = None
    strategy_reuse: Optional[bool] = None
    agent_performance_learning: Optional[bool] = None
    regression_intelligence: Optional[bool] = None
    prompt_optimization: Optional[bool] = None

@app.get("/api/intelligence/status")
def get_intelligence_status():
    return intelligence_engine.get_status()

@app.get("/api/intelligence/profile")
def get_intelligence_profile(workspace: Optional[str] = None):
    ws = workspace or current_config.get("workspace", DEFAULT_WORKSPACE)
    return intelligence_engine.get_profile(ws)

@app.get("/api/intelligence/experiences")
def get_intelligence_experiences(task_type: Optional[str] = None, outcome: Optional[str] = None, limit: int = 50):
    return [e.to_dict() for e in intelligence_engine.experience_retriever.list_experiences(task_type=task_type, outcome=outcome, limit=limit)]

@app.get("/api/intelligence/patterns")
def get_intelligence_patterns(limit: int = 50):
    return [p.to_dict() for p in intelligence_engine.pattern_engine.list_all(limit=limit)]

@app.get("/api/intelligence/strategies")
def get_intelligence_strategies(status: Optional[str] = None, limit: int = 50):
    return [s.to_dict() for s in intelligence_engine.strategy_engine.list_strategies(status=status, limit=limit)]

@app.get("/api/intelligence/predictions")
def get_intelligence_predictions(limit: int = 20):
    return [p.to_dict() for p in intelligence_engine.prediction_engine.list_predictions(limit=limit)]

@app.get("/api/intelligence/performance")
def get_intelligence_performance():
    return intelligence_engine.agent_performance.list_all_performance()

@app.get("/api/intelligence/regressions")
def get_intelligence_regressions(component: Optional[str] = None):
    return [r.to_dict() for r in intelligence_engine.regression_detector.get_unresolved_regressions(component=component)]

@app.get("/api/intelligence/events")
def get_intelligence_events(limit: int = 50):
    return intelligence_engine.learning_engine.list_events(limit=limit)

@app.get("/api/intelligence/graph")
def get_intelligence_graph():
    return intelligence_engine.knowledge_engine.export_graph_json()

@app.post("/api/intelligence/preflight")
def post_intelligence_preflight(req: PreflightIntelRequest):
    ws = req.workspace or current_config.get("workspace", DEFAULT_WORKSPACE)
    curr_sess = session_manager.current_session
    s_id = req.session_id or (curr_sess.session_id if curr_sess else None)
    res = intelligence_engine.run_preflight(
        task=req.task,
        workspace=ws,
        session_id=s_id,
        agent_id=req.agent_id
    )
    return res.to_dict()

@app.post("/api/intelligence/explain")
def post_intelligence_explain(req: IntelExplainRequest):
    return intelligence_engine.explain_decision(req.topic, req.identifier)

@app.post("/api/intelligence/learn")
def post_intelligence_learn(req: IntelLearnRequest):
    curr_sess = session_manager.current_session
    s_id = req.session_id or (curr_sess.session_id if curr_sess else "")
    p_id = req.project_id or "default"
    if req.rejected_entity:
        return intelligence_engine.learning_engine.learn_user_correction(
            rejected_entity=req.rejected_entity,
            accepted_alternative=req.accepted_alternative,
            reason=req.reason or "Explicit API correction",
            session_id=s_id,
            project_id=p_id
        )
    elif req.user_text:
        return intelligence_engine.process_user_correction(
            user_text=req.user_text,
            session_id=s_id,
            project_id=p_id
        )
    return {"status": "no_op", "detail": "Specify rejected_entity or user_text"}

@app.get("/api/intelligence/settings")
def get_intelligence_settings():
    return intelligence_engine.settings

@app.post("/api/intelligence/settings")
def update_intelligence_settings(req: IntelSettingsUpdateRequest):
    updates = {k: v for k, v in req.dict().items() if v is not None}
    return intelligence_engine.update_settings(updates)


# ----------------- SKILLS EXPLORER -----------------
@app.get("/api/skills")
def get_all_skills():
    """Discover all portable and user skills dynamically."""
    import re
    categorized = {
        "Pédagogie & Formation (ATAM)": [],
        "Vibe Coding & Fullstack": [],
        "Deep Thinking & Stratégie": [],
        "Création & Multimédia": [],
        "Autonomie & Workflows": [],
        "Cloud & DevOps": [],
        "Autres Compétences": []
    }
    
    seen_ids = set()
    skills_folders = [SKILLS_DIR, Path.home() / ".gemini" / "skills"]
    
    for base in skills_folders:
        if not base.exists():
            continue
        for sf in base.glob("**/SKILL.md"):
            try:
                rel = sf.parent.relative_to(base)
                skill_id = str(rel).replace("\\", "/")
                if skill_id in seen_ids:
                    continue
                seen_ids.add(skill_id)
                
                content = sf.read_text(encoding="utf-8", errors="ignore")
                m = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
                name = skill_id.split("/")[-1].replace("-", " ").title()
                desc = "Compétence agentique prête à l'emploi."
                if m:
                    fm = m.group(1)
                    nm = re.search(r"name:\s*(.+)", fm)
                    if nm:
                        name = nm.group(1).strip()
                    dm = re.search(r"description:\s*(?:>-\s*|\"|\|)?\s*(.+?)(?:\n\w+:|$)", fm, re.DOTALL)
                    if dm:
                        desc = " ".join(dm.group(1).replace("\n", " ").split())
                
                item = {"id": skill_id, "name": name, "desc": desc[:160]}
                sid_lower = skill_id.lower()
                
                if any(k in sid_lower for k in ["cahier", "pedagog", "atam", "eval-fiche", "classeur"]):
                    categorized["Pédagogie & Formation (ATAM)"].append(item)
                elif any(k in sid_lower for k in ["react", "frontend", "ui-ux", "tailwind", "next", "vue", "node", "web"]):
                    categorized["Vibe Coding & Fullstack"].append(item)
                elif any(k in sid_lower for k in ["brainstorm", "boost", "plan", "grill", "think", "audit", "reason"]):
                    categorized["Deep Thinking & Stratégie"].append(item)
                elif any(k in sid_lower for k in ["image", "video", "media", "art", "music", "audio", "draw"]):
                    categorized["Création & Multimédia"].append(item)
                elif any(k in sid_lower for k in ["autonomy", "agent", "workflow", "subagent", "queue", "worker"]):
                    categorized["Autonomie & Workflows"].append(item)
                elif any(k in sid_lower for k in ["cloud", "docker", "k8s", "aws", "azure", "gcp", "vps"]):
                    categorized["Cloud & DevOps"].append(item)
                else:
                    categorized["Autres Compétences"].append(item)
            except Exception:
                continue
                
    result = {k: v for k, v in categorized.items() if v}
    return result if result else {"Compétences": [{"id": "cahierdetext", "name": "Cahier de Texte Certifié", "desc": "Génération officielle"}]}

# ----------------- CREATIVE STUDIO (IMAGES & VIDEO) -----------------
class GenerateMediaRequest(BaseModel):
    prompt: str
    media_type: str = "image"
    aspect_ratio: str = "16:9"

@app.get("/api/media")
def list_media():
    items = []
    for f in MEDIA_DIR.glob("*.*"):
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".svg", ".mp4", ".webp"]:
            items.append({
                "name": f.name,
                "url": f"/api/media/raw/{f.name}",
                "path": str(f),
                "created": f.stat().st_mtime,
                "size": f.stat().st_size
            })
    items.sort(key=lambda x: x["created"], reverse=True)
    return items

@app.get("/api/media/raw/{filename}")
def get_media_file(filename: str):
    f = MEDIA_DIR / filename
    if not f.exists():
        raise HTTPException(status_code=404, detail="Média introuvable")
    ext = f.suffix.lower()
    media_type = "application/octet-stream"
    if ext == ".svg": media_type = "image/svg+xml"
    elif ext in [".png", ".webp"]: media_type = f"image/{ext[1:]}"
    elif ext in [".jpg", ".jpeg"]: media_type = "image/jpeg"
    elif ext == ".mp4": media_type = "video/mp4"
    return FileResponse(str(f), media_type=media_type)

@app.post("/api/media/generate")
def generate_media_asset(req: GenerateMediaRequest):
    timestamp = int(time.time())
    slug = re.sub(r'[^a-zA-Z0-9]', '_', req.prompt[:30]).strip('_').lower() or "asset"
    asset_base = f"{req.media_type}_{slug}_{timestamp}"
    ws = Path(current_config.get("workspace", DEFAULT_WORKSPACE))
    ws.mkdir(parents=True, exist_ok=True)

    # 1. Detect aspect ratio and resolution
    p_lower = req.prompt.lower()
    if "1080x1350" in p_lower or "4:5" in p_lower or "portrait" in p_lower:
        w, h = 1080, 1350
    elif "1920x1080" in p_lower or "16:9" in p_lower or req.aspect_ratio == "16:9":
        w, h = 1280, 720
    elif "9:16" in p_lower or "story" in p_lower or "reel" in p_lower:
        w, h = 1080, 1920
    else:
        # Default Instagram square
        w, h = 1080, 1080

    # 2. Render real image using Pillow
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter

        # Check if we have an existing realistic photo in media or workspace to base from
        sample_photos = list(MEDIA_DIR.glob("*.jpg")) + list(MEDIA_DIR.glob("*.png"))
        matching_photo = None
        for sp in sample_photos:
            if "till" in sp.name or "assistant" in sp.name or "qatar" in sp.name:
                matching_photo = sp
                break

        if matching_photo and matching_photo.exists():
            base_img = Image.open(matching_photo).convert("RGBA")
            base_img = base_img.resize((w, h), Image.Resampling.LANCZOS)
        else:
            # Create rich luxury ambient background with subtle gradients
            base_img = Image.new("RGBA", (w, h), (10, 15, 28, 255))
            d_bg = ImageDraw.Draw(base_img)
            for y in range(h):
                ratio = y / float(h)
                r = int(10 + 20 * ratio)
                g = int(15 + 25 * ratio)
                b = int(28 + 45 * ratio)
                d_bg.line([(0, y), (w, y)], fill=(r, g, b, 255))

            import random
            random.seed(timestamp)
            bokeh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d_bk = ImageDraw.Draw(bokeh)
            for _ in range(12):
                bx = random.randint(50, w - 50)
                by = random.randint(50, h - 50)
                br = random.randint(60, 180)
                d_bk.ellipse([(bx - br, by - br), (bx + br, by + br)], fill=(56, 189, 248, 25))
            bokeh = bokeh.filter(ImageFilter.GaussianBlur(35))
            base_img = Image.alpha_composite(base_img, bokeh)

        # Graphic overlay with card and clean typography
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Top banner for contrast
        for y in range(160):
            alpha = int(140 * (1.0 - y / 160.0))
            draw.line([(0, y), (w, y)], fill=(10, 15, 30, alpha))

        # Bottom dark glassmorphism gradient
        bottom_start = int(h * 0.65)
        for y in range(bottom_start, h):
            progress = (y - bottom_start) / float(h - bottom_start)
            alpha = int(230 * (progress ** 0.8))
            draw.line([(0, y), (w, y)], fill=(5, 10, 22, alpha))

        # Extract title and info
        lines = [line.strip() for line in req.prompt.split("\n") if line.strip()]
        first_line = lines[0] if lines else req.prompt[:40]
        title_text = first_line.split("|")[0].strip() if "|" in first_line else first_line[:30]

        # Tag pill
        draw.rounded_rectangle([(50, 40), (380, 80)], radius=10, fill=(15, 23, 42, 210), outline=(56, 189, 248, 120), width=1)
        draw.text((65, 52), "CAREER OPPORTUNITY", fill=(56, 189, 248, 255))

        # Title
        draw.text((60, h - 280), title_text.upper()[:35], fill=(255, 255, 255, 255))
        draw.text((60, h - 235), "Hamad International Airport • Customer Service & Retail", fill=(148, 163, 184, 255))

        # Feature pills
        pills = ["Full-Time Role", "Premium Experience", "Safe Cash Handling"]
        px = 60
        for p in pills:
            pw = len(p) * 8 + 24
            draw.rounded_rectangle([(px, h - 180), (px + pw, h - 146)], radius=8, fill=(30, 41, 59, 220), outline=(71, 85, 105, 160), width=1)
            draw.text((px + 12, h - 170), p, fill=(241, 245, 249, 255))
            px += pw + 12

        # CTA
        draw.rounded_rectangle([(w - 280, h - 130), (w - 60, h - 70)], radius=12, fill=(14, 165, 233, 240))
        draw.text((w - 210, h - 108), "APPLY NOW", fill=(255, 255, 255, 255))

        final_img = Image.alpha_composite(base_img, overlay).convert("RGB")
        out_png = MEDIA_DIR / f"{asset_base}.png"
        final_img.save(out_png, "PNG", quality=95)

        # Also copy to workspace
        ws_copy = ws / f"{asset_base}.png"
        final_img.save(ws_copy, "PNG", quality=95)

        # Also generate companion SVG with embedded base64 image
        import base64
        b64_data = base64.b64encode(out_png.read_bytes()).decode("ascii")
        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%">
  <image width="{w}" height="{h}" href="data:image/png;base64,{b64_data}"/>
</svg>'''
        out_svg = MEDIA_DIR / f"{asset_base}.svg"
        out_svg.write_text(svg_content, encoding="utf-8")
        (ws / f"{asset_base}.svg").write_text(svg_content, encoding="utf-8")

        # Ingest into artifact manager
        try:
            artifact_manager.ingest_file(
                source=out_png,
                name=out_png.name,
                session_id=None
            )
        except Exception:
            pass

        return {
            "status": "created",
            "filename": out_png.name,
            "url": f"/api/media/raw/{out_png.name}",
            "workspace_path": str(ws_copy),
            "dimensions": f"{w}x{h}",
            "prompt": req.prompt,
            "media_type": "image/png"
        }

    except Exception as ex:
        out_file = MEDIA_DIR / f"{asset_base}.svg"
        out_file.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="#0f172a"/><text x="50" y="100" fill="#fff">{req.prompt[:50]}</text></svg>', encoding="utf-8")
        return {
            "status": "created",
            "filename": out_file.name,
            "url": f"/api/media/raw/{out_file.name}",
            "prompt": req.prompt,
            "media_type": "image/svg+xml"
        }

# ----------------- TASKS & QUEUE -----------------
@app.get("/api/queue")
def get_task_queue():
    ws = Path(current_config.get("workspace", DEFAULT_WORKSPACE))
    queue_file = ws / "tasks" / "QUEUE.md"
    if not queue_file.exists():
        return {"error": "tasks/QUEUE.md introuvable", "sections": {}}

    try:
        with open(queue_file, "r", encoding="utf-8") as f:
            content = f.read()

        sections = {"Ready": [], "In Progress": [], "Blocked": [], "Done Today": []}
        curr = None
        for line in content.splitlines():
            s = line.strip()
            if s.startswith("## "):
                sec = s[3:].split("(")[0].strip()
                if "Ready" in sec: curr = "Ready"
                elif "In Progress" in sec: curr = "In Progress"
                elif "Blocked" in sec: curr = "Blocked"
                elif "Done" in sec: curr = "Done Today"
                else: curr = None
            elif curr and (s.startswith("- [ ]") or s.startswith("- [x]")):
                checked = s.startswith("- [x]")
                text = s[5:].strip()
                priority = "normal"
                if "[CRITICAL]" in text.upper(): priority = "critical"
                elif "[HIGH]" in text.upper(): priority = "high"
                sections[curr].append({"text": text, "checked": checked, "priority": priority})

        return {"sections": sections, "file_path": str(queue_file)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- FILES & ARTIFACT PREVIEW -----------------
@app.get("/api/files")
def list_workspace_files(subdir: str = "", filter_type: str = "all"):
    ws = Path(current_config.get("workspace", DEFAULT_WORKSPACE))
    target_dir = ws / subdir if subdir else ws
    if not target_dir.exists() or not target_dir.is_dir():
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    items = []
    try:
        for entry in os.scandir(target_dir):
            if entry.name.startswith(".") and entry.name != ".":
                continue
            rel_path = os.path.relpath(entry.path, str(ws))
            stat = entry.stat()
            ext = os.path.splitext(entry.name)[1].lower()
            items.append({
                "name": entry.name,
                "path": os.path.abspath(entry.path),
                "rel_path": rel_path.replace("\\", "/"),
                "is_dir": entry.is_dir(),
                "size": stat.st_size if not entry.is_dir() else 0,
                "modified": stat.st_mtime,
                "extension": ext if not entry.is_dir() else "dir"
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return {
        "current_dir": str(target_dir),
        "workspace": str(ws),
        "items": items
    }

@app.get("/api/file/raw")
def get_raw_file(path: str = Query(..., description="Chemin absolu ou relatif")):
    ws = Path(current_config.get("workspace", DEFAULT_WORKSPACE))
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = ws / file_path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    ext = file_path.suffix.lower()
    media_type = "application/octet-stream"
    if ext == ".pdf": media_type = "application/pdf"
    elif ext in [".docx", ".doc"]: media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ext in [".txt", ".py", ".md", ".json", ".js", ".ts", ".html"]: media_type = "text/plain; charset=utf-8"
    elif ext in [".png", ".jpg", ".jpeg", ".webp"]: media_type = f"image/{ext[1:]}"
    elif ext == ".svg": media_type = "image/svg+xml"

    return FileResponse(str(file_path), media_type=media_type, filename=file_path.name)

class OpenExternalRequest(BaseModel):
    path: Optional[str] = ""

@app.post("/api/file/open_external")
def open_file_external(req: OpenExternalRequest):
    ws_str = current_config.get("workspace", DEFAULT_WORKSPACE)
    ws = Path(ws_str)
    raw_target = (req.path or "").strip()
    clean_target = raw_target.split("?")[0].strip()

    p = None

    # 1. Direct check for /api/media/raw/<filename>
    if "/api/media/raw/" in clean_target:
        fname = clean_target.split("/api/media/raw/")[-1].lstrip("/")
        cand = MEDIA_DIR / fname
        if cand.exists(): p = cand
    elif clean_target.startswith("/api/media/"):
        fname = clean_target.split("/")[-1]
        cand = MEDIA_DIR / fname
        if cand.exists(): p = cand

    # 2. Check if clean_target is an existing absolute path
    if not p and os.path.exists(clean_target):
        p = Path(clean_target)

    # 3. Check inside MEDIA_DIR by basename
    if not p:
        cand = MEDIA_DIR / os.path.basename(clean_target)
        if cand.exists(): p = cand

    # 4. Check inside active workspace
    if not p and clean_target:
        cand = ws / clean_target.lstrip("/\\")
        if cand.exists(): p = cand

    # 5. Check inside workspace by basename
    if not p and clean_target:
        cand = ws / os.path.basename(clean_target)
        if cand.exists(): p = cand

    # 6. Check artifact manager
    if not p:
        try:
            art = artifact_manager.get_artifact(clean_target)
            if art:
                cand = getattr(art, "path", None) or getattr(art, "file_path", None)
                if cand and Path(cand).exists():
                    p = Path(cand)
        except Exception:
            pass

    # 7. Fallback to workspace directory if still not resolved
    if not p:
        if ws.exists():
            p = ws
        else:
            raise HTTPException(status_code=404, detail=f"Fichier ou dossier introuvable : {clean_target}")

    # Launch in native Windows application
    try:
        if hasattr(os, "startfile"):
            try:
                os.startfile(str(p))
                return {"status": "opened", "path": str(p)}
            except Exception as e_start:
                # If file type has no association, show in Windows Explorer
                subprocess.Popen(["explorer.exe", f"/select,{str(p)}"])
                return {"status": "opened_explorer", "path": str(p), "note": str(e_start)}
        else:
            subprocess.Popen(["explorer", str(p)])
            return {"status": "opened", "path": str(p)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'ouverture système : {e}")

@app.get("/api/file/preview")
def get_file_preview(path: str = Query(..., description="Chemin absolu du fichier")):
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = Path(current_config.get("workspace", DEFAULT_WORKSPACE)) / file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    ext = file_path.suffix.lower()
    stat = file_path.stat()
    safe_encoded_path = urllib.parse.quote(str(file_path))

    # Resolve structured preview through centralized PreviewService
    p_res = preview_service.resolve_file_preview(file_path)

    pdf_companion = None
    if ext == ".docx":
        candidate_pdf = file_path.with_suffix(".pdf")
        if candidate_pdf.exists():
            pdf_companion = f"/api/file/raw?path={urllib.parse.quote(str(candidate_pdf))}"

    result = {
        "name": file_path.name,
        "path": str(file_path),
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "extension": ext,
        "preview_enabled": p_res.get("preview_enabled", True),
        "preview_type": p_res.get("preview_type", "none"),
        "preview_mode": p_res.get("preview_mode", "NATIVE"),
        "content": p_res.get("content", ""),
        "content_url": p_res.get("content_url", f"/api/file/raw?path={safe_encoded_path}"),
        "raw_url": f"/api/file/raw?path={safe_encoded_path}",
        "has_pdf_companion": pdf_companion is not None,
        "pdf_companion_url": pdf_companion,
        "sheets": p_res.get("sheets", []),
        "sheet_names": p_res.get("sheet_names", []),
        "slides": p_res.get("slides", []),
        "slide_count": p_res.get("slide_count", 0),
        "security": p_res.get("security", {"allowed": True, "quarantined": False})
    }

    # Backward-compatible content string for text/pdf/image if not set
    if result["preview_type"] == "pdf" and not result["content"]:
        result["content"] = f"/api/file/raw?path={safe_encoded_path}"
    elif result["preview_type"] == "image" and not result["content"]:
        result["content"] = f"/api/file/raw?path={safe_encoded_path}"

    return result

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    ws = Path(current_config.get("workspace", DEFAULT_WORKSPACE))
    uploads_dir = ws / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    target_path = uploads_dir / file.filename
    with open(target_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {
        "filename": file.filename,
        "path": str(target_path),
        "size": target_path.stat().st_size
    }

def is_shell_command(text: str) -> bool:
    t = text.strip()
    shell_prefixes = (
        "&", "powershell", "python", "dir", "ls", "cd", "cat", "git", 
        "taskkill", "uv", "Get-", "Set-", "Start-", "Stop-", "npm", "node", 
        "echo", "mkdir", "rm", "del", "type", "cls", "clear", "findstr"
    )
    if t.startswith(shell_prefixes):
        return True
    if t.startswith(r"C:\\") or t.startswith(r"D:\\") or t.startswith(".\\"):
        return True
    return False

# ----------------- COMMAND EXECUTION & AGENT ENGINE -----------------
class CommandRequest(BaseModel):
    command: str
    approved: bool = False
    action_type: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    thinking_mode: Optional[str] = "turbo"
    new_thread: bool = False
    recursion_depth: int = 0
    parent_agent_id: Optional[str] = None
    artifact_ids: Optional[List[str]] = None
    session_id: Optional[str] = None

class LocalToolRequest(BaseModel):
    tool: str
    target: Optional[str] = None

@app.post("/api/session/reset")
def reset_session():
    mem = load_memory()
    items = mem.setdefault("categories", {}).setdefault("Historique de Contexte", [])
    items.insert(0, {
        "id": f"sess_{int(time.time())}",
        "title": f"Fil réinitialisé le {time.strftime('%Y-%m-%d %H:%M')}",
        "content": "Contexte de session archivé et remis à zéro pour préserver les quotas.",
        "tag": "RESET",
        "created_at": time.strftime("%Y-%m-%d %H:%M")
    })
    save_memory(mem)
    return {"status": "success", "message": "Nouveau fil démarré. Tokens réinitialisés à 0."}

@app.post("/api/tools/local")
def execute_local_tool(req: LocalToolRequest):
    tool = req.tool
    ws = Path(current_config.get("workspace", DEFAULT_WORKSPACE))

    def run_stream():
        yield f"data: {json.dumps({'type': 'start', 'command': f'[OUTIL LOCAL] {tool}'})}\n\n"
        try:
            if tool == "clean_locks":
                folder = Path(r"D:\Piopi\Cahier text\Planning année 2025-2027\Classeur formateur")
                yield f"data: {json.dumps({'type': 'chunk', 'text': f' Nettoyage des verrous temporaires Word dans {folder}...\n'})}\n\n"
                cleaned = 0
                if folder.exists():
                    for lock in folder.glob("~$*"):
                        try:
                            lock.unlink(missing_ok=True)
                            yield f"data: {json.dumps({'type': 'chunk', 'text': f'  ✓ Supprimé : {lock.name}\n'})}\n\n"
                            cleaned += 1
                        except Exception as e:
                            yield f"data: {json.dumps({'type': 'chunk', 'text': f'  Erreur sur {lock.name}: {e}\n'})}\n\n"
                yield f"data: {json.dumps({'type': 'chunk', 'text': f' Terminé : {cleaned} fichier(s) temporaire(s) nettoyé(s) (0 token consommé).\n'})}\n\n"

            elif tool == "audit_classeurs":
                yield f"data: {json.dumps({'type': 'chunk', 'text': ' Lancement de l\'audit d\'intégrité des 7 classeurs formateurs (0 token)...\n\n'})}\n\n"
                script = STUDIO_ROOT / "scripts" / "inspect_t0_all.py"
                p = subprocess.run([UV_PATH, "run", "--with", "python-docx", "python", str(script)], capture_output=True, text=True, encoding="utf-8")
                for line in p.stdout.splitlines():
                    yield f"data: {json.dumps({'type': 'chunk', 'text': line + '\n'})}\n\n"
                yield f"data: {json.dumps({'type': 'chunk', 'text': '\n Audit terminé avec succès sans consommer de tokens !\n'})}\n\n"

            elif tool == "open_workspace":
                yield f"data: {json.dumps({'type': 'chunk', 'text': f' Ouverture de l\'explorateur Windows sur le Workspace : {ws}...\n'})}\n\n"
                os.startfile(str(ws))
                yield f"data: {json.dumps({'type': 'chunk', 'text': '✓ Explorateur ouvert.\n'})}\n\n"

            elif tool == "open_timetables":
                tt = Path(r"D:\Piopi\Cahier text\Planning année 2025-2027")
                yield f"data: {json.dumps({'type': 'chunk', 'text': f' Ouverture du dossier officiel des plannings : {tt}...\n'})}\n\n"
                if tt.exists():
                    os.startfile(str(tt))
                    yield f"data: {json.dumps({'type': 'chunk', 'text': '✓ Dossier ouvert dans Windows.\n'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'chunk', 'text': ' Dossier introuvable sur le disque D:\n'})}\n\n"

            elif tool == "git_diff":
                yield f"data: {json.dumps({'type': 'chunk', 'text': ' Différences Git en cours dans le Workspace...\n\n'})}\n\n"
                p = subprocess.run(["git", "diff", "--stat"], cwd=str(ws), capture_output=True, text=True, encoding="utf-8")
                diff_text = p.stdout.strip()
                if diff_text:
                    yield f"data: {json.dumps({'type': 'chunk', 'text': diff_text + '\n'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'chunk', 'text': 'Arbre de travail propre (aucun fichier modifié non validé).\n'})}\n\n"

            elif tool == "git_status":
                yield f"data: {json.dumps({'type': 'chunk', 'text': ' Statut des fichiers modifiés (Git)...\n\n'})}\n\n"
                p = subprocess.run(["git", "status", "-s"], cwd=str(ws), capture_output=True, text=True, encoding="utf-8")
                out_txt = p.stdout.strip() or "Aucun fichier modifié (dépôt synchronisé)."
                yield f"data: {json.dumps({'type': 'chunk', 'text': out_txt + '\n'})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'returncode': 0, 'full_output': ''})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(run_stream(), media_type="text/event-stream")

MAX_AGENT_DEPTH = 3

@app.post("/api/execute/stream")
def execute_command_stream(req: CommandRequest):
    auth_mode = current_config.get("authorization_mode", "permanent")
    now = time.time()
    is_temp_valid = (auth_mode == "temporary" and current_config.get("temp_auth_until", 0) > now)

    if auth_mode == "ask" and not req.approved:
        return JSONResponse({
            "status": "needs_confirmation",
            "message": "Cette commande nécessite votre approbation manuelle (mode 'Toujours demander' actif).",
            "command": req.command
        })
    if auth_mode == "temporary" and not is_temp_valid and not req.approved:
        return JSONResponse({
            "status": "needs_confirmation",
            "message": "L'autorisation temporaire a expiré. Veuillez autoriser la commande.",
            "command": req.command
        })

    if getattr(req, "recursion_depth", 0) >= MAX_AGENT_DEPTH:
        def err_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': 'MAX_AGENT_DEPTH exceeded'})}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    ws = Path(current_config.get("workspace", DEFAULT_WORKSPACE))
    cmd = req.command.strip()
    selected_model = current_config.get("model", "gemini-3.8-flash-medium")

    def stream_slash_command(handler_fn):
        def event_stream():
            yield f"data: {json.dumps({'type': 'start', 'command': cmd})}\n\n"
            try:
                for chunk in handler_fn():
                    yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'returncode': 0, 'full_output': ''})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    if cmd.startswith("/quota"):
        def handle_quota():
            yield " Interrogation en direct des quotas d'utilisation Antigravity...\n\n"
            q = get_live_quota()
            if q["items"]:
                for item in q["items"]:
                    pct = item["percent"]
                    bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
                    yield f"[{item['provider']}] {item['name']}\n"
                    yield f"   Capacité restante: {pct}% [{bar}]\n"
                    if item.get("reset"):
                        yield f"   Réinitialisation : {item['reset']}\n\n"
            else:
                yield q["raw"] + "\n"
        return stream_slash_command(handle_quota)

    if cmd.startswith("/model"):
        def handle_model():
            parts = cmd.split()
            if len(parts) > 1:
                target_model = parts[1].strip()
                current_config["model"] = target_model
                save_config(current_config)
                persist_model_to_settings(target_model)
                yield f"<div class='p-3 bg-sky-950/70 border border-sky-500/50 rounded-xl space-y-1 my-2'>"
                yield f"  <div class='text-xs font-bold text-sky-300 flex items-center gap-1.5'> Modèle actif basculé avec succès sur : <span class='font-mono text-emerald-400'>{target_model}</span></div>"
                yield f"  <div class='text-[10px] text-slate-400'>Synchronisé avec ~/.gemini/antigravity-cli/settings.json et Agy Studio.</div>"
                yield f"</div>"
            else:
                m_info = get_models()
                curr = m_info.get("current_model", "gemini-3.8-flash-medium")
                yield f"<div class='space-y-3 my-2 font-sans'>"
                yield f"  <div class='flex items-center justify-between bg-slate-950/90 p-3 rounded-xl border border-slate-800'>"
                yield f"    <span class='text-xs text-slate-300 font-medium'>Modèle actuellement actif :</span>"
                yield f"    <span class='text-xs font-bold font-mono px-3 py-1 bg-sky-950 text-sky-300 border border-sky-600/60 rounded-lg'>{curr}</span>"
                yield f"  </div>"
                yield f"  <div class='text-xs font-bold text-slate-200 flex items-center justify-between'>"
                yield f"    <span>Cliquez sur un modèle pour l'activer instantanément :</span>"
                yield f"    <span class='text-[10px] text-slate-400 font-normal'>14 modèles disponibles</span>"
                yield f"  </div>"
                yield f"  <div class='grid grid-cols-1 sm:grid-cols-2 gap-2'>"
                for m in m_info["models"]:
                    is_active = m["id"] == curr
                    active_cls = "border-sky-500 bg-sky-950/50 shadow-md ring-1 ring-sky-500/30" if is_active else "border-slate-800/90 bg-slate-950 hover:bg-slate-800/80 hover:border-slate-700"
                    badge = "<span class='text-[9px] bg-sky-500 text-black px-1.5 py-0.5 rounded font-bold uppercase'>Actif</span>" if is_active else "<span class='text-[10px] text-sky-400 group-hover:underline'>Activer &rarr;</span>"
                    yield f"    <button onclick=\"changeAgentModel('{m['id']}')\" class='p-2.5 rounded-xl border text-left flex items-center justify-between transition group cursor-pointer {active_cls}'>"
                    yield f"      <div>"
                    yield f"        <div class='text-xs font-semibold text-slate-200 group-hover:text-sky-300'>{m['name']}</div>"
                    yield f"        <div class='text-[10px] font-mono text-slate-500'>{m['id']}</div>"
                    yield f"      </div>"
                    yield f"      <div>{badge}</div>"
                    yield f"    </button>"
                yield f"  </div>"
                yield f"</div>"
        return stream_slash_command(handle_model)

    if cmd.startswith("/mcp"):
        def handle_mcp():
            yield "🔌 **État des serveurs MCP connectés (Model Context Protocol) :**\n\n"
            servers = mcp_manager.list_servers() if mcp_manager else get_mcp_servers()
            for s in servers:
                status = s.get("status", "unknown")
                is_enabled = s.get("enabled", True)
                if status in ["connected", "active"] and is_enabled:
                    status_icon = "🟢"
                elif is_enabled:
                    status_icon = "🟡"
                else:
                    status_icon = "⚪"
                
                name = s.get("name", "inconnu")
                cat = (s.get("category") or s.get("type") or "mcp").upper()
                st_label = f"{status}" + (" (Activé)" if is_enabled else " (Désactivé)")
                yield f"{status_icon} **{name}** `[{cat}]` : *{st_label}*\n"
                if s.get("description"):
                    yield f"   📝 {s['description']}\n"
                if s.get("url"):
                    yield f"   🌐 URL : `{s['url']}`\n"
                if s.get("command"):
                    yield f"   ⚙️ Commande : `{s['command']}`\n"
                
                tools = s.get("tools", [])
                if tools:
                    tool_names = [t.get("name") if isinstance(t, dict) else str(t) for t in tools]
                    yield f"   🛠️ **Outils disponibles ({len(tools)})** : `{', '.join(tool_names)}`\n"
                yield "\n"
            yield "---\n"
            yield "💡 **Gestionnaire MCP Agy Studio** : Ouvrez le menu **Actions > 🔌 Serveurs MCP** ou cliquez sur le bouton ci-dessous pour configurer, tester et connecter WordPress, VPS ou GitHub en temps réel.\n\n"
            yield "<div class='mt-2'><button onclick='if(typeof toggleMcpModal===\"function\"){toggleMcpModal();}else{document.getElementById(\"mcpModal\").classList.remove(\"hidden\");}' class='px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold shadow-md transition inline-flex items-center gap-1.5 cursor-pointer'>🔌 Ouvrir le Gestionnaire MCP</button></div>\n"
        return stream_slash_command(handle_mcp)

    if cmd.startswith("/plugins"):
        def handle_plugins():
            yield " État des plugins installés :\n\n"
            pl = get_plugins()
            yield pl["raw"] + "\n"
        return stream_slash_command(handle_plugins)

    if cmd.startswith("/open "):
        def handle_open():
            target = cmd[6:].strip().strip('"').strip("'")
            yield f" Ouverture directe dans l'application Windows : {target}\n"
            try:
                os.startfile(target)
                yield "Application lancée avec succès !\n"
            except Exception as e:
                yield f" Erreur : {e}\n"
        return stream_slash_command(handle_open)

    if cmd.startswith("/help"):
        def handle_help():
            yield " **Commandes disponibles dans Agy Studio :**\n\n"
            yield "• `/quota` : Affiche l'état réel et en direct de vos quotas Gemini, Claude et GPT.\n"
            yield "• `/model` : Affiche la liste des modèles ou `/model <id>` pour basculer.\n"
            yield "• `/mcp` : Inspecte les serveurs Model Context Protocol connectés.\n"
            yield "• `/plugins` : Liste les plugins agy installés.\n"
            yield "• `/open <chemin>` : Ouvre n'importe quel fichier Word, PDF ou dossier dans Windows.\n"
            yield "• `/plan <requête>` : Lance une décomposition stratégique autonome.\n"
            yield "• `/boost <requête>` : Active le mode de raisonnement multi-perspectives.\n"
            yield "• `/clear` : Réinitialise l'affichage du terminal et du chat.\n"
        return stream_slash_command(handle_help)

    # Inject Multimodal Artifact Context if attached
    if req.artifact_ids:
        art_contexts = []
        for aid in req.artifact_ids:
            art = artifact_manager.get_artifact(aid)
            if art:
                session_manager.attach_artifact(art.id, art.name, art.mime_type, art.size_bytes)
                art_contexts.append(art.to_prompt_context())
        if art_contexts:
            cmd = f"{cmd}\n\n=== CONTEXTE ARTEFACTS MULTIMODAUX INGESTES ===\n" + "\n".join(art_contexts)

    # Ensure active session exists
    curr_sess = session_manager.get_current_session()
    if not curr_sess:
        curr_sess = session_manager.create_session(workspace=str(ws))

    # 1. Automated Learning from user text (corrections, rejections, architectural rules)
    memory_manager.learn_from_user(
        cmd,
        session_id=curr_sess.session_id,
        workspace=str(ws)
    )

    # Attach task to current session timeline
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    session_manager.attach_task(task_id=task_id, prompt=cmd)

    # 2. Anti-Repetition Guard: prevent re-proposing rejected approaches
    guard_res = memory_manager.check_guard(
        cmd,
        workspace=str(ws),
        session_id=curr_sess.session_id
    )
    if guard_res.violation and not guard_res.allowed:
        def stream_guard_rejection():
            yield f"data: {json.dumps({'type': 'start', 'command': req.command, 'model': selected_model})}\n\n"
            msg = f"\n{guard_res.warning}\n"
            yield f"data: {json.dumps({'type': 'chunk', 'text': msg})}\n\n"
            session_manager.attach_execution(
                command=req.command,
                agent_name="memory_guard",
                status="BLOCKED_BY_GUARD",
                return_code=1
            )
            yield f"data: {json.dumps({'type': 'done', 'returncode': 1, 'full_output': msg})}\n\n"
        return StreamingResponse(stream_guard_rejection(), media_type="text/event-stream")

    # 3. Pre-flight Memory Retrieval
    preflight = memory_manager.preflight_check(
        task=cmd,
        workspace=str(ws),
        session_id=curr_sess.session_id
    )

    if req.action_type == "build_all_classeurs":
        # Resolve classeur build script: check workspace/scripts/, then STUDIO_ROOT/scripts/
        exec_script = ws / "scripts" / "execute_and_verify.py"
        if not exec_script.exists():
            exec_script = STUDIO_ROOT / "scripts" / "execute_and_verify.py"
        cmd_args = ["powershell.exe", "-NoProfile", "-Command", f'& "{UV_PATH}" run --with python-docx --with pywin32 --with pypdf python "{exec_script}"']
    elif req.action_type == "check_queue":
        script = ws / "tasks" / "check_queue.py"
        cmd_args = ["powershell.exe", "-NoProfile", "-Command", f'& "{UV_PATH}" run python "{script}"']
    elif not is_shell_command(cmd) and not req.action_type and os.path.exists(AGY_EXE):
        # Inject Adaptive Intelligence Preflight if available
        agent_input = cmd
        try:
            adaptive_preflight = intelligence_engine.run_preflight(task=cmd, workspace=str(ws), session_id=curr_sess.session_id)
            if adaptive_preflight and adaptive_preflight.markdown:
                agent_input = f"{adaptive_preflight.markdown}\n\n{cmd}"
        except Exception:
            if preflight.context_injection_markdown:
                agent_input = f"{preflight.context_injection_markdown}\n\n{cmd}"
        cmd_args = [
            AGY_EXE,
            "-p", agent_input,
            "--model", selected_model,
            "--dangerously-skip-permissions",
            "--add-dir", str(ws)
        ]
    else:
        cmd_args = ["powershell.exe", "-NoProfile", "-Command", cmd]

    def event_stream():
        yield f"data: {json.dumps({'type': 'start', 'command': req.command, 'model': selected_model})}\n\n"
        # If preflight had critical corrections or rejected items, notify the stream
        if preflight.has_critical_corrections or preflight.has_rejected_approaches:
            notice = f"[MÉMOIRE ACTIVE] {len(preflight.corrections)} corrections et {len(preflight.rejected_approaches)} approches rejetées appliquées au contexte.\n"
            yield f"data: {json.dumps({'type': 'chunk', 'text': notice})}\n\n"

        try:
            proc = subprocess.Popen(
                cmd_args,
                cwd=str(ws),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace"
            )
            collected_lines = []
            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line:
                    collected_lines.append(line)
                    yield f"data: {json.dumps({'type': 'chunk', 'text': line})}\n\n"
            proc.wait()
            full_out = "".join(collected_lines)
            
            # Record execution in active session correlation tree
            exec_id = f"exec_{uuid.uuid4().hex[:8]}"
            session_manager.attach_execution(
                execution_id=exec_id,
                task_id=task_id,
                command=req.command,
                agent_name="antigravity" if os.path.exists(AGY_EXE) and not is_shell_command(cmd) else "powershell",
                status="COMPLETED" if proc.returncode == 0 else "FAILED",
                return_code=proc.returncode,
                artifact_ids=req.artifact_ids or []
            )

            # Record outcome in Intelligence Engine & Learning Memory
            try:
                intelligence_engine.record_execution_outcome(
                    task=cmd,
                    exit_code=proc.returncode,
                    stdout_text=full_out,
                    agent_id="antigravity" if os.path.exists(AGY_EXE) and not is_shell_command(cmd) else "powershell",
                    session_id=curr_sess.session_id,
                    project_id=curr_sess.project_id if hasattr(curr_sess, "project_id") else "default",
                    workspace=str(ws),
                    task_id=task_id
                )
            except Exception as e:
                logging.warning(f"Error recording intelligence outcome: {e}")

            if proc.returncode != 0 and len(full_out.strip()) > 0:
                memory_manager.record_outcome(
                    task=cmd,
                    approach_summary="",
                    success=False,
                    exit_code=proc.returncode,
                    error_message=full_out[-300:],
                    session_id=curr_sess.session_id,
                    workspace=str(ws),
                    evidence_ref=exec_id
                )
            
            yield f"data: {json.dumps({'type': 'done', 'returncode': proc.returncode, 'full_output': full_out})}\n\n"
        except Exception as e:
            session_manager.record_event("EXECUTION_ERROR", {"error": str(e), "command": req.command})
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ----------------- PLAYWRIGHT INTEGRATION -----------------
class PlaywrightRequest(BaseModel):
    url: str
    action: str = "screenshot"
    script: Optional[str] = None

_pw_instance = None
_pw_browser = None

async def get_playwright_browser():
    global _pw_instance, _pw_browser
    from playwright.async_api import async_playwright
    if not _pw_instance:
        _pw_instance = await async_playwright().start()
    if not _pw_browser:
        _pw_browser = await _pw_instance.chromium.launch(headless=True)
    return _pw_browser

@app.post("/api/playwright/run")
async def run_playwright(req: PlaywrightRequest):
    try:
        import playwright
    except ImportError:
        return JSONResponse({"status": "error", "message": "Playwright n'est pas installé."}, status_code=500)
    
    try:
        browser = await get_playwright_browser()
        page = await browser.new_page()
        await page.goto(req.url, wait_until="networkidle", timeout=30000)
        
        result = {}
        if req.action == "screenshot":
            ts = int(time.time())
            out_name = f"playwright_{ts}.png"
            out_path = MEDIA_DIR / out_name
            await page.screenshot(path=str(out_path), full_page=False)
            result["screenshot_url"] = f"/api/media/raw/{out_name}"
            result["status"] = "success"
        elif req.action == "extract":
            content = await page.evaluate("document.body.innerText")
            result["content"] = content
            result["status"] = "success"
        elif req.action == "script":
            if req.script:
                script_code = req.script.strip()
                if script_code.startswith("()") or script_code.startswith("async ()") or script_code.startswith("function"):
                    eval_res = await page.evaluate(script_code)
                else:
                    eval_res = await page.evaluate(f"async () => {{ {script_code} }}")
                result["script_result"] = eval_res
            result["status"] = "success"
        
        await page.close()
        return result
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# ----------------- USAGE STATS -----------------
session_stats = {
    "session_start": time.time(),
    "messages": [],
    "total_tokens": 0
}

class StatsMessage(BaseModel):
    role: str
    char_count: int
    est_tokens: int

@app.post("/api/usage/stats")
def add_usage_stat(msg: StatsMessage):
    session_stats["messages"].append({
        "role": msg.role,
        "char_count": msg.char_count,
        "est_tokens": msg.est_tokens,
        "timestamp": time.time()
    })
    session_stats["total_tokens"] += msg.est_tokens
    return {"status": "success"}

@app.get("/api/usage/stats")
def get_usage_stats():
    duration_mins = (time.time() - session_stats["session_start"]) / 60
    return {
        "session_start": session_stats["session_start"],
        "messages": session_stats["messages"],
        "total_tokens": session_stats["total_tokens"],
        "session_duration_minutes": duration_mins
    }

# ----------------- WEB FETCH -----------------
import urllib.request
@app.get("/api/web/fetch")
def web_fetch(url: str = Query(...)):
    try:
        req = urllib.request.Request(
            url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8', errors='replace')
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            title = title_match.group(1) if title_match else url
            return {"status": "success", "content": content, "title": title, "url": url}
    except Exception as e:
        return {"status": "error", "message": str(e), "url": url}

# ----------------- FILE MANAGEMENT -----------------
class RenameRequest(BaseModel):
    path: str
    new_name: str

@app.post("/api/file/rename")
def file_rename(req: RenameRequest):
    p = Path(req.path)
    if not p.is_absolute():
        p = Path(current_config.get("workspace", DEFAULT_WORKSPACE)) / p
    if not p.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    new_path = p.parent / req.new_name
    try:
        p.rename(new_path)
        return {"status": "success", "new_path": str(new_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DeleteRequest(BaseModel):
    path: str

@app.delete("/api/file/delete")
def file_delete(req: DeleteRequest):
    p = Path(req.path)
    if not p.is_absolute():
        p = Path(current_config.get("workspace", DEFAULT_WORKSPACE)) / p
    if not p.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------- STATIC FRONTEND -----------------
STATIC_DIR = STUDIO_ROOT / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(
            str(index_file),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return HTMLResponse("<h1>Agy Studio v2.5 - Démarrage...</h1>")

# ----------------- AGENT REGISTRY & UNIVERSAL CLI ORCHESTRATOR ENDPOINTS -----------------
@app.api_route("/api/agents/discover", methods=["GET", "POST"])
def discover_agents():
    agents = agent_registry.discover_all()
    return {"status": "success", "agents": agents}

@app.get("/api/agents")
def get_agents():
    return agent_registry.list_agents()

@app.get("/api/agents/{agent_id}")
def get_agent_detail(agent_id: str):
    ag = agent_registry.get_agent(agent_id)
    if not ag:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' introuvable")
    return ag

class VerifyAgentRequest(BaseModel):
    provider_id: Optional[str] = None
    timeout: Optional[int] = 35

@app.post("/api/agents/{agent_id}/verify")
def verify_agent_operational(
    agent_id: str,
    req: Optional[VerifyAgentRequest] = None,
    provider_id: Optional[str] = None,
    timeout: Optional[int] = 35
):
    prov = (req.provider_id if req else None) or provider_id
    to = (req.timeout if req else None) or timeout or 35
    try:
        res = agent_registry.verify_agent(agent_id, provider_id=prov, timeout=to)
        return {"status": "success", "agent": res}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=400, detail=str(fe))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Échec de vérification opérationnelle : {ex}")

@app.get("/api/agents/{agent_id}/health")
def get_agent_health(agent_id: str):
    ag = agent_registry.get_agent(agent_id)
    if not ag:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return {
        "id": agent_id,
        "name": ag.get("name"),
        "status": ag.get("status"),
        "health": ag.get("health", {}),
        "authentication": ag.get("authentication", {}),
        "version_evidence": ag.get("version_evidence"),
        "operational_evidence": ag.get("operational_evidence"),
        "last_checked": ag.get("last_checked"),
        "last_verified": ag.get("last_verified")
    }

@app.get("/api/agents/{agent_id}/capabilities")
def get_agent_capabilities(agent_id: str):
    ag = agent_registry.get_agent(agent_id)
    if not ag:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return {
        "id": agent_id,
        "status": ag.get("status"),
        "capabilities": ag.get("capabilities", {})
    }

class CustomAgentRequest(BaseModel):
    name: str
    command: str
    path: Optional[str] = None
    version_args: Optional[List[str]] = None
    test_args: Optional[List[str]] = None
    prompt_mode: Optional[str] = "argument"
    timeout: Optional[int] = 120
    roles: Optional[List[str]] = None
    declared_capabilities: Optional[Dict[str, bool]] = None

@app.post("/api/agents/custom")
def register_custom_agent(req: CustomAgentRequest):
    try:
        res = agent_registry.add_custom_agent(
            name=req.name,
            command=req.command,
            custom_path=req.path,
            version_args=req.version_args,
            test_args=req.test_args,
            prompt_mode=req.prompt_mode or "argument",
            timeout=req.timeout or 120,
            roles=req.roles,
            declared_capabilities=req.declared_capabilities
        )
        return {"status": "success", "agent": res}
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.delete("/api/agents/custom/{agent_id}")
def remove_custom_agent(agent_id: str):
    ok = agent_registry.delete_custom_agent(agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent personnalisé introuvable")
    return {"status": "success", "deleted": agent_id}

# --- INJECTED CODE START ---
import uuid
import hashlib
import threading

# Agent role binding handled below (single authoritative implementation)

class ExecutionRunRequest(BaseModel):
    agent_id: str
    task_id: str
    project_id: str
    command: str
    working_directory: str
    parent_execution_id: Optional[str] = None
    timeout_seconds: Optional[int] = None

EXECUTIONS_FILE = DATA_DIR / "executions.json"
def load_executions():
    if EXECUTIONS_FILE.exists():
        with open(EXECUTIONS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {}
def save_executions(data):
    with open(EXECUTIONS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)

def _run_execution_bg(exec_id, cmd, cwd, timeout):
    exs = load_executions()
    if exec_id not in exs: return
    exs[exec_id]["status"] = "RUNNING"
    save_executions(exs)
    try:
        proc = subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", cmd], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        exs = load_executions()
        exs[exec_id]["pid"] = proc.pid
        save_executions(exs)
        
        stdout, stderr = proc.communicate(timeout=timeout)
        exs = load_executions()
        if exs[exec_id]["status"] != "CANCELLED":
            exs[exec_id]["status"] = "COMPLETED" if proc.returncode == 0 else "FAILED"
            exs[exec_id]["stdout"] = stdout
            exs[exec_id]["stderr"] = stderr
            exs[exec_id]["exit_code"] = proc.returncode
            exs[exec_id]["end_time"] = time.time()
            save_executions(exs)
    except subprocess.TimeoutExpired:
        proc.kill()
        exs = load_executions()
        exs[exec_id]["status"] = "FAILED"
        exs[exec_id]["stderr"] = "Timeout"
        exs[exec_id]["end_time"] = time.time()
        save_executions(exs)
    except Exception as e:
        exs = load_executions()
        if exs[exec_id]["status"] != "CANCELLED":
            exs[exec_id]["status"] = "FAILED"
            exs[exec_id]["stderr"] = str(e)
            exs[exec_id]["end_time"] = time.time()
            save_executions(exs)

@app.post("/api/executions/run")
def run_execution(req: ExecutionRunRequest):
    exec_id = f"exec_{uuid.uuid4().hex[:8]}"
    exs = load_executions()
    exs[exec_id] = {
        "execution_id": exec_id, "agent_id": req.agent_id, "task_id": req.task_id,
        "project_id": req.project_id, "parent_execution_id": req.parent_execution_id,
        "command": req.command, "working_directory": req.working_directory,
        "pid": None, "start_time": time.time(), "end_time": None,
        "exit_code": None, "stdout": "", "stderr": "", "status": "STARTING", "artifacts": []
    }
    save_executions(exs)
    threading.Thread(target=_run_execution_bg, args=(exec_id, req.command, req.working_directory, req.timeout_seconds), daemon=True).start()
    return {"execution_id": exec_id, "pid": None, "status": "STARTING"}

@app.get("/api/executions")
def get_executions(project_id: Optional[str] = None, task_id: Optional[str] = None, status: Optional[str] = None):
    exs = load_executions()
    res = list(exs.values())
    if project_id: res = [x for x in res if x.get("project_id") == project_id]
    if task_id: res = [x for x in res if x.get("task_id") == task_id]
    if status: res = [x for x in res if x.get("status") == status]
    return res

@app.get("/api/executions/{execution_id}")
def get_execution(execution_id: str):
    exs = load_executions()
    if execution_id not in exs: raise HTTPException(status_code=404)
    return exs[execution_id]

@app.post("/api/executions/{execution_id}/cancel")
def cancel_execution(execution_id: str):
    exs = load_executions()
    if execution_id not in exs: raise HTTPException(status_code=404, detail="Execution not found")
    ex = exs[execution_id]
    cancellation_evidence = {
        "pid": ex.get("pid"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "process_state": "TERMINATED",
        "exit_code": -1
    }
    if ex.get("status") in ["RUNNING", "STARTING"]:
        pid = ex.get("pid")
        if pid:
            try:
                p = subprocess.run(["taskkill.exe", "/F", "/T", "/PID", str(pid)], capture_output=True, text=True)
                cancellation_evidence["kill_exit_code"] = p.returncode
                cancellation_evidence["kill_output"] = p.stdout.strip()
            except Exception as ke:
                cancellation_evidence["kill_error"] = str(ke)
        ex["status"] = "CANCELLED"
        ex["end_time"] = time.time()
        ex["cancellation_evidence"] = cancellation_evidence
        save_executions(exs)
    return {"status": "CANCELLED", "execution_id": execution_id, "evidence": cancellation_evidence}

@app.get("/api/executions/stream/{execution_id}")
def stream_execution(execution_id: str):
    def event_stream():
        yield f"data: {json.dumps({'type': 'chunk', 'text': 'Streaming not fully implemented for subprocess yet'})}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")

TASKS_FILE = DATA_DIR / "tasks.json"
def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {}
def save_tasks(data):
    with open(TASKS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)

class TaskCreate(BaseModel):
    project_id: str
    title: str
    description: str = ""
    priority: str = "NORMAL"
    agent_id: Optional[str] = None
    dependencies: Optional[List[str]] = []

@app.post("/api/tasks")
def create_task(req: TaskCreate):
    tasks = load_tasks()
    tid = f"task_{uuid.uuid4().hex[:8]}"
    now = time.time()
    task = {
        "task_id": tid, "project_id": req.project_id,
        "title": req.title, "description": req.description,
        "priority": req.priority, "agent_id": req.agent_id,
        "dependencies": req.dependencies or [],
        "status": "PENDING", "input": "", "output": "",
        "artifacts": [], "errors": [],
        "created_at": now, "updated_at": now
    }
    tasks[tid] = task
    save_tasks(tasks)
    return task

@app.get("/api/tasks")
def list_p2_tasks(project_id: Optional[str] = None):
    tasks = load_tasks()
    result = list(tasks.values())
    if project_id:
        result = [t for t in result if t.get("project_id") == project_id]
    return result

@app.patch("/api/tasks/{task_id}")
def update_task(task_id: str, updates: Dict[str, Any]):
    tasks = load_tasks()
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks[task_id].update(updates)
    tasks[task_id]["updated_at"] = time.time()
    save_tasks(tasks)
    return tasks[task_id]

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    tasks = load_tasks()
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    save_tasks(tasks)
    return {"status": "deleted", "task_id": task_id}

@app.post("/api/tasks/scheduler/run")
def scheduler_run():
    tasks = load_tasks()
    queued, blocked, running = [], [], []
    for tid, t in tasks.items():
        if t.get("status") == "COMPLETED": continue
        deps = t.get("dependencies", [])
        deps_completed = all(tasks.get(d, {}).get("status") == "COMPLETED" for d in deps)
        if deps_completed:
            if t.get("status") == "RUNNING": running.append(t)
            else: queued.append(t)
        else:
            blocked.append(t)
    return {"queued": queued, "blocked": blocked, "running": running}

PROJECTS_FILE = DATA_DIR / "projects.json"
def load_projects():
    if PROJECTS_FILE.exists():
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {}
def save_projects(data):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)

class ProjectCreate(BaseModel):
    name: str
    description: str
    workspace: str
    assigned_agents: Optional[List[str]] = []

@app.get("/api/projects")
def get_projects():
    return list(load_projects().values())

@app.post("/api/projects")
def create_project(req: ProjectCreate):
    projs = load_projects()
    pid = f"proj_{uuid.uuid4().hex[:8]}"
    now = time.time()
    projs[pid] = {
        "project_id": pid, "name": req.name, "description": req.description,
        "workspace": req.workspace, "assigned_agents": req.assigned_agents,
        "created": now, "modified": now, "status": "ACTIVE"
    }
    save_projects(projs)
    return projs[pid]

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workspace: Optional[str] = None
    status: Optional[str] = None

@app.patch("/api/projects/{project_id}")
def update_project(project_id: str, req: ProjectUpdate):
    projs = load_projects()
    if project_id not in projs: raise HTTPException(404)
    p = projs[project_id]
    if req.name: p["name"] = req.name
    if req.description: p["description"] = req.description
    if req.workspace: p["workspace"] = req.workspace
    if req.status: p["status"] = req.status
    p["modified"] = time.time()
    save_projects(projs)
    return p

@app.delete("/api/projects/{project_id}")
def archive_project(project_id: str):
    projs = load_projects()
    if project_id not in projs: raise HTTPException(404)
    projs[project_id]["status"] = "ARCHIVED"
    projs[project_id]["modified"] = time.time()
    save_projects(projs)
    return projs[project_id]

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    projs = load_projects()
    if project_id not in projs: raise HTTPException(404)
    
    tasks = load_tasks()
    p_tasks = [t for t in tasks.values() if t.get("project_id") == project_id]
    
    arts = []
    if ARTIFACTS_FILE.exists():
        try:
            with open(ARTIFACTS_FILE, "r") as f: arts = json.load(f)
        except Exception:
            pass
    p_arts = [a for a in arts if a.get("project_id") == project_id]
    
    mem = load_memory()
    structured = mem.get("structured_memories", [])
    p_mem = [m for m in structured if m.get("project_id") == project_id]
    
    return {"project": projs[project_id], "tasks": p_tasks, "artifacts": p_arts, "memory": p_mem}

@app.get("/api/projects/{project_id}/tasks")
def get_project_tasks(project_id: str):
    tasks = load_tasks()
    return [t for t in tasks.values() if t.get("project_id") == project_id]

@app.get("/api/projects/{project_id}/artifacts")
def get_project_artifacts(project_id: str):
    arts = []
    if ARTIFACTS_FILE.exists():
        try:
            with open(ARTIFACTS_FILE, "r") as f: arts = json.load(f)
        except Exception:
            pass
    return [a for a in arts if a.get("project_id") == project_id]

@app.get("/api/projects/{project_id}/memory")
def get_project_memory(project_id: str):
    mem = load_memory()
    structured = mem.get("structured_memories", [])
    return [m for m in structured if m.get("project_id") == project_id]

SWARM_FILE = DATA_DIR / "swarm.json"
class SwarmCreate(BaseModel):
    objective: str
    agent_ids: List[str]
    project_id: str

@app.post("/api/swarm/create")
def create_swarm(req: SwarmCreate):
    swarms = {}
    if SWARM_FILE.exists():
        with open(SWARM_FILE, "r", encoding="utf-8") as f: swarms = json.load(f)

    # ORCHESTRATOR ENFORCEMENT: validate each requested agent is OPERATIONAL
    from backend.agent_adapters.base import AgentStatus as _AgentStatus
    agents_data = agent_registry._load_data().get("agents", {})
    rejected_agents = []
    approved_agent_ids = []
    for aid in req.agent_ids:
        ag_dict = agents_data.get(aid)
        if not ag_dict:
            rejected_agents.append({"agent_id": aid, "reason": "Agent not found in registry"})
        elif ag_dict.get("status") not in [_AgentStatus.OPERATIONAL.value]:
            rejected_agents.append({"agent_id": aid, "reason": f"Agent status is {ag_dict.get('status')}; must be OPERATIONAL to join swarm"})
        else:
            approved_agent_ids.append(aid)

    if rejected_agents:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ORCHESTRATOR_ENFORCEMENT: One or more agents are not OPERATIONAL and cannot be assigned to a swarm.",
                "rejected": rejected_agents,
                "approved": approved_agent_ids,
                "rule": "Agy Studio MUST NEVER assign a task to an agent that has not passed the required OPERATIONAL capability test."
            }
        )

    sid = f"swarm_{uuid.uuid4().hex[:8]}"
    tasks = []

    if len(approved_agent_ids) > 1:
        for i, aid in enumerate(approved_agent_ids):
            tasks.append({"task_id": f"t_{sid}_{i}", "agent_id": aid, "status": "QUEUED"})
    else:
        aid = approved_agent_ids[0] if approved_agent_ids else "default"
        tasks.append({"task_id": f"t_{sid}_0", "agent_id": aid, "status": "QUEUED"})

    s = {"swarm_id": sid, "objective": req.objective, "agents": approved_agent_ids, "tasks": tasks, "status": "ACTIVE", "created_at": time.time()}
    swarms[sid] = s
    with open(SWARM_FILE, "w", encoding="utf-8") as f: json.dump(swarms, f, indent=2)
    return s

@app.get("/api/swarm/{swarm_id}")
def get_swarm(swarm_id: str):
    swarms = {}
    if SWARM_FILE.exists():
        with open(SWARM_FILE, "r") as f: swarms = json.load(f)
    if swarm_id not in swarms: raise HTTPException(404)
    return swarms[swarm_id]

@app.post("/api/swarm/{swarm_id}/cancel")
def cancel_swarm(swarm_id: str):
    swarms = {}
    if SWARM_FILE.exists():
        with open(SWARM_FILE, "r") as f: swarms = json.load(f)
    if swarm_id not in swarms: raise HTTPException(404)
    swarms[swarm_id]["status"] = "CANCELLED"
    with open(SWARM_FILE, "w", encoding="utf-8") as f: json.dump(swarms, f, indent=2)
    return {"status": "CANCELLED"}

MESSAGES_FILE = DATA_DIR / "messages.json"
class AgentMessage(BaseModel):
    sender_agent_id: str
    receiver_agent_id: str
    task_id: str
    execution_id: str
    type: str
    payload: str

@app.post("/api/messages")
def post_message(req: AgentMessage):
    msgs = []
    if MESSAGES_FILE.exists():
        with open(MESSAGES_FILE, "r") as f: msgs = json.load(f)
    m = req.dict()
    m["message_id"] = f"msg_{uuid.uuid4().hex[:8]}"
    m["created_at"] = time.time()
    msgs.append(m)
    with open(MESSAGES_FILE, "w") as f: json.dump(msgs, f, indent=2)
    return m

@app.get("/api/messages")
def get_messages(task_id: Optional[str] = None, agent_id: Optional[str] = None, type: Optional[str] = None):
    msgs = []
    if MESSAGES_FILE.exists():
        with open(MESSAGES_FILE, "r") as f: msgs = json.load(f)
    if task_id: msgs = [m for m in msgs if m.get("task_id") == task_id]
    if agent_id: msgs = [m for m in msgs if m.get("sender_agent_id") == agent_id or m.get("receiver_agent_id") == agent_id]
    if type: msgs = [m for m in msgs if m.get("type") == type]
    return msgs

class MemoryLearnReq(BaseModel):
    execution_id: str
    task_id: str
    project_id: str
    agent_id: str

@app.post("/api/memory/learn")
def memory_learn(req: MemoryLearnReq):
    exs = load_executions()
    if req.execution_id not in exs: raise HTTPException(404)
    ex = exs[req.execution_id]
    out = (ex.get("stdout") or "") + (ex.get("stderr") or "")
    
    category = "SEMANTIC"
    confidence = 0.6
    if "Error:" in out or "failed" in out:
        category = "FAILURE"
        confidence = 0.9
    elif "Successfully" in out or "Created" in out:
        category = "PROCEDURAL"
        confidence = 0.8
        
    mem = load_memory()
    structured = mem.setdefault("structured_memories", [])
    m_id = f"mem_{uuid.uuid4().hex[:8]}"
    structured.append({
        "memory_id": m_id,
        "category": category,
        "content": out[:500],
        "source_task": req.task_id,
        "source_agent": req.agent_id,
        "project_id": req.project_id,
        "confidence": confidence,
        "importance": 0.5,
        "created_at": time.time(),
        "updated_at": time.time(),
        "last_used_at": time.time(),
        "usage_count": 0,
        "validation_status": "UNVALIDATED"
    })
    save_memory(mem)
    return {"status": "learned", "memory_id": m_id}

@app.get("/api/memory/retrieve")
def memory_retrieve(task_description: str, project_id: str, limit: int = 5):
    mem = load_memory()
    structured = mem.get("structured_memories", [])
    relevant = [m for m in structured if m.get("project_id") == project_id]
    results = []
    words = set(task_description.lower().split())
    for m in relevant:
        content_words = set(m.get("content", "").lower().split())
        if words.intersection(content_words):
            m["last_used_at"] = time.time()
            m["usage_count"] = m.get("usage_count", 0) + 1
            results.append(m)
    save_memory(mem)
    results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    return results[:limit]

@app.post("/api/memory/consolidate")
def memory_consolidate():
    mem = load_memory()
    structured = mem.get("structured_memories", [])
    
    merged = 0
    promoted = 0
    invalidated = 0
    
    seen = {}
    new_structured = []
    
    now = time.time()
    
    for m in structured:
        if now - m.get("last_used_at", 0) > 30*24*3600:
            invalidated += 1
            continue
            
        h = hashlib.md5(m.get("content", "").encode()).hexdigest()
        if h in seen:
            merged += 1
            idx = seen[h]
            if m.get("confidence", 0) > new_structured[idx].get("confidence", 0):
                new_structured[idx]["confidence"] = m.get("confidence", 0)
            new_structured[idx]["usage_count"] += m.get("usage_count", 0)
        else:
            seen[h] = len(new_structured)
            new_structured.append(m)
            
    for m in new_structured:
        if m.get("usage_count", 0) > 5:
            m["category"] = "GLOBAL"
            promoted += 1
            
    mem["structured_memories"] = new_structured
    save_memory(mem)
    return {"merged": merged, "promoted": promoted, "invalidated": invalidated}

class MemoryFailReq(BaseModel):
    error_description: str
    solution: str
    task_id: str
    agent_id: str
    project_id: str

@app.post("/api/memory/failure")
def memory_failure(req: MemoryFailReq):
    mem = load_memory()
    structured = mem.setdefault("structured_memories", [])
    m_id = f"mem_{uuid.uuid4().hex[:8]}"
    structured.append({
        "memory_id": m_id,
        "category": "FAILURE",
        "content": f"Error: {req.error_description} Solution: {req.solution}",
        "source_task": req.task_id,
        "source_agent": req.agent_id,
        "project_id": req.project_id,
        "confidence": 1.0,
        "importance": 1.0,
        "created_at": time.time(),
        "updated_at": time.time(),
        "last_used_at": time.time(),
        "usage_count": 0,
        "validation_status": "VALIDATED"
    })
    save_memory(mem)
    return {"memory_id": m_id}

ARTIFACTS_FILE = DATA_DIR / "artifacts.json"
class ArtifactReq(BaseModel):
    project_id: str
    task_id: str
    agent_id: str
    path: str

@app.post("/api/artifacts/register")
def register_artifact(req: ArtifactReq):
    if not os.path.exists(req.path): raise HTTPException(400, detail="File not found")
    arts = []
    if ARTIFACTS_FILE.exists():
        try:
            with open(ARTIFACTS_FILE, "r") as f: arts = json.load(f)
        except Exception:
            pass
    a = req.dict()
    a["checksum"] = hashlib.md5(open(req.path, "rb").read()).hexdigest()
    a["size"] = os.path.getsize(req.path)
    a["type"] = os.path.splitext(req.path)[1]
    a["created_at"] = time.time()
    arts.append(a)
    with open(ARTIFACTS_FILE, "w") as f: json.dump(arts, f, indent=2)
    return a

# ================= UNIVERSAL ARTIFACT API =================
@app.post("/api/artifacts/upload")
async def upload_artifacts(files: List[UploadFile] = File(...), session_id: Optional[str] = Query(None)):
    sess_id = session_id or (session_manager.get_current_session().session_id if session_manager.get_current_session() else "default")
    ingested = []
    for file in files:
        data = await file.read()
        art = artifact_manager.ingest_file(
            source=data,
            filename=file.filename,
            acquisition=ArtifactAcquisition.DRAG_DROP,
            session_id=sess_id
        )
        ingested.append(art.to_summary_dict())
    return {"status": "ok", "count": len(ingested), "artifacts": ingested}

class ClipboardPasteRequest(BaseModel):
    data_base64: Optional[str] = None
    mime_type: Optional[str] = None
    filename: Optional[str] = None
    text: Optional[str] = None
    session_id: Optional[str] = None

@app.post("/api/artifacts/clipboard")
async def post_artifacts_clipboard(req: Optional[ClipboardPasteRequest] = None):
    sess_id = (req.session_id if req else None) or (session_manager.get_current_session().session_id if session_manager.get_current_session() else "default")

    if req and req.data_base64:
        import base64
        try:
            raw_b64 = req.data_base64
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            b_data = base64.b64decode(raw_b64)
            fn = req.filename or f"pasted_image_{int(time.time())}.png"
            art = artifact_manager.ingest_file(
                source=b_data,
                filename=fn,
                acquisition=ArtifactAcquisition.PASTE,
                session_id=sess_id
            )
            dim_str = f"{art.metadata.width}×{art.metadata.height}" if art.metadata.width else ""
            mb_str = f"{art.size_bytes / (1024*1024):.1f} MB" if art.size_bytes >= 1024*1024 else f"{art.size_bytes / 1024:.0f} KB"
            return {
                "status": "ok",
                "message": f"✓ Capture d'écran enregistrée ({dim_str} • {mb_str})",
                "artifact": art.to_summary_dict()
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erreur d'ingestion base64 : {e}")

    if req and req.text:
        art = artifact_manager.ingest_file(
            source=req.text.encode("utf-8"),
            filename=f"pasted_text_{int(time.time())}.txt",
            acquisition=ArtifactAcquisition.PASTE,
            session_id=sess_id
        )
        return {
            "status": "ok",
            "message": f"✓ Texte du presse-papiers ingéré ({len(req.text)} caractères)",
            "artifact": art.to_summary_dict()
        }

    # Query native desktop clipboard
    art, msg = artifact_manager.ingest_clipboard(session_id=sess_id)
    if not art:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "status": "ok",
        "message": msg,
        "artifact": art.to_summary_dict()
    }

@app.get("/api/artifacts")
def get_artifacts(
    session_id: Optional[str] = None,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    agent_id: Optional[str] = None
):
    # Retrieve universal artifacts for session
    sess_id = session_id or (session_manager.get_current_session().session_id if session_manager.get_current_session() else None)
    univ_arts = [a.to_summary_dict() for a in artifact_manager.list_artifacts(session_id=sess_id)]

    # Include legacy artifacts if project_id or task_id specified
    legacy_arts = []
    if ARTIFACTS_FILE.exists():
        try:
            with open(ARTIFACTS_FILE, "r") as f: legacy_arts = json.load(f)
        except Exception:
            pass
        if project_id: legacy_arts = [a for a in legacy_arts if a.get("project_id") == project_id]
        if task_id: legacy_arts = [a for a in legacy_arts if a.get("task_id") == task_id]
        if agent_id: legacy_arts = [a for a in legacy_arts if a.get("agent_id") == agent_id]

    if legacy_arts and not session_id:
        return univ_arts + legacy_arts
    return univ_arts

@app.get("/api/artifacts/{artifact_id}")
def get_artifact_by_id(artifact_id: str):
    art = artifact_manager.get_artifact(artifact_id)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact introuvable")
    return art.model_dump()

@app.get("/api/preview/config")
def get_preview_config():
    """Returns centralized preview configuration and safe support matrix (Section 5 & 7A)."""
    return {
        "preview_enabled": REAL_PREVIEW_ENABLED,
        "max_size_bytes": PREVIEW_MAX_SIZE,
        "support_matrix": PREVIEW_SUPPORT_MATRIX,
        "version": "2.6.0"
    }

@app.get("/api/artifacts/{artifact_id}/preview")
def get_artifact_preview_endpoint(
    artifact_id: str,
    request: Request,
    raw: bool = Query(False, description="Retourner directement le flux binaire/image")
):
    """
    Centralized Real Preview endpoint.
    Returns rich preview payload, or raw binary stream for images/PDFs if requested.
    """
    art = artifact_manager.get_artifact(artifact_id)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact introuvable")

    accept = request.headers.get("accept", "")
    is_img = art.source_type in (ArtifactSourceType.IMAGE, ArtifactSourceType.SCREENSHOT, ArtifactSourceType.CLIPBOARD_IMAGE)

    # Direct image stream if requested by raw parameter or standard <img> tag
    if raw or (is_img and "image/" in accept and "application/json" not in accept):
        img_p = art.content.image_path or art.content.binary_path
        if os.path.exists(img_p):
            return FileResponse(img_p, media_type=art.mime_type)

    # Structured preview resolution via PreviewService
    p_data = preview_service.resolve_artifact_preview(artifact_id)
    return p_data

@app.get("/api/artifacts/{artifact_id}/preview/raw")
def get_artifact_preview_raw_stream(artifact_id: str):
    """
    Returns sandboxed raw file stream with strict security headers (Section 27).
    Used for native PDF viewer and sandboxed HTML/SVG previews.
    """
    art = artifact_manager.get_artifact(artifact_id)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact introuvable")
    bin_p = Path(art.content.binary_path)
    if not bin_p.exists():
        raise HTTPException(status_code=404, detail="Fichier binaire manquant")

    # Security headers
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-cache, no-store, must-revalidate"
    }
    if art.extension.lower() in (".html", ".htm", ".svg"):
        headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"

    return FileResponse(
        str(bin_p),
        media_type=art.mime_type,
        headers=headers,
        filename=art.name
    )

@app.get("/api/artifacts/{artifact_id}/content")
def get_artifact_content_endpoint(artifact_id: str):
    art = artifact_manager.get_artifact(artifact_id)
    if not art or not os.path.exists(art.content.binary_path):
        raise HTTPException(status_code=404, detail="Artifact introuvable ou fichier manquant")
    return FileResponse(art.content.binary_path, media_type=art.mime_type, filename=art.name)

@app.delete("/api/artifacts/{artifact_id}")
def delete_artifact_endpoint(artifact_id: str):
    ok = artifact_manager.delete_artifact(artifact_id)
    return {"status": "deleted" if ok else "error"}

def is_playwright_available() -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec("playwright") is not None
    except Exception:
        return False

@app.get("/api/health")
def get_health():
    return {
        "status": "OK", "timestamp": time.time(),
        "checks": {
            "backend": {"status": "OK", "detail": "responding"},
            "agents": {"status": "OK", "detail": len(load_agents().get("agents", {}))},
            "playwright": {"status": "OK" if is_playwright_available() else "NOT_INSTALLED", "detail": ""},
            "projects_db": {"status": "OK" if PROJECTS_FILE.exists() else "MISSING", "detail": ""},
            "tasks_db": {"status": "OK" if TASKS_FILE.exists() else "MISSING", "detail": ""},
            "executions_db": {"status": "OK" if EXECUTIONS_FILE.exists() else "MISSING", "detail": ""},
            "memory_db": {"status": "OK" if MEMORY_FILE.exists() else "MISSING", "detail": ""}
        }
    }

@app.get("/api/diagnostics")
def get_diagnostics():
    def f_size(p):
        return os.path.getsize(p) if p.exists() else 0
        
    exs = load_executions()
    mem = load_memory()
    
    return {
        "studio_root_integrity": {
            "server.py": (STUDIO_ROOT / "backend" / "server.py").exists(),
            "index.html": (STUDIO_ROOT / "static" / "index.html").exists()
        },
        "backend_version": "2.5.0",
        "python_version": sys.version,
        "data_file_sizes": {
            "agents.json": f_size(AGENTS_FILE),
            "projects.json": f_size(PROJECTS_FILE),
            "tasks.json": f_size(TASKS_FILE),
            "executions.json": f_size(EXECUTIONS_FILE),
            "memory.json": f_size(MEMORY_FILE)
        },
        "agents": {
            "count": len(load_agents().get("agents", {})),
            "list": [{"name": a.get("name"), "status": a.get("status")} for a in load_agents().get("agents", {}).values()]
        },
        "executions": {
            "total": len(exs),
            "running": len([e for e in exs.values() if e.get("status") == "RUNNING"]),
            "failed": len([e for e in exs.values() if e.get("status") == "FAILED"])
        },
        "memory": {
            "count": len(mem.get("structured_memories", []))
        },
        "playwright": {
            "installed": is_playwright_available()
        },
        "agy_exe": {
            "exists": os.path.exists(AGY_EXE)
        },
        "hermes": {
            "exists": bool(subprocess.run(["where.exe", "hermes"], capture_output=True).stdout)
        }
    }

class PlaywrightAgentTaskReq(BaseModel):
    task_id: str
    project_id: str
    action: str
    url: str
    selector: Optional[str] = None
    script: Optional[str] = None
    inject_to_agent_context: Optional[bool] = False

@app.post("/api/playwright/agent-task")
async def playwright_agent_task(req: PlaywrightAgentTaskReq):
    res = await run_playwright(PlaywrightRequest(url=req.url, action=req.action, script=req.script))
    if req.inject_to_agent_context and res.get("status") == "success":
        art_path = str(MEDIA_DIR / f"playwright_context_{int(time.time())}.txt")
        with open(art_path, "w") as f:
            f.write(json.dumps(res))
        register_artifact(ArtifactReq(project_id=req.project_id, task_id=req.task_id, agent_id="playwright", path=art_path))
        res["artifact_path"] = art_path
    return res
class BindRoleRequest(BaseModel):
    role: str
    enabled: bool

@app.post("/api/agents/{agent_id}/bind")
def bind_agent_role(agent_id: str, req: BindRoleRequest):
    try:
        return agent_registry.bind_role(agent_id, req.role, req.enabled)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


# --- INJECTED CODE END ---

# =========== ORCHESTRATOR ROUTES ===========

class OrchestratorSelectRequest(BaseModel):
    role: str
    required_capabilities: Optional[List[str]] = None
    preferred_agent: Optional[str] = None
    preferred_provider: Optional[str] = None
    allow_unverified: bool = False
    task_id: Optional[str] = None

@app.post("/api/orchestrator/select")
def orchestrator_select(req: OrchestratorSelectRequest):
    """
    Select the best OPERATIONAL agent for a given role and capability set.
    Returns selection decision evidence (selected agent + rejection reasons).
    """
    selected, decision = agent_orchestrator.select_agent(
        role=req.role,
        required_capabilities=req.required_capabilities,
        preferred_agent=req.preferred_agent,
        preferred_provider=req.preferred_provider,
        allow_unverified=req.allow_unverified,
        task_id=req.task_id
    )
    return {
        "selected_agent": selected.dict() if selected else None,
        "decision": decision.to_dict()
    }

class OrchestratorExecuteRequest(BaseModel):
    task_id: str
    prompt: str
    role: str
    workspace: Optional[str] = None
    required_capabilities: Optional[List[str]] = None
    preferred_agent: Optional[str] = None
    preferred_provider: Optional[str] = None
    allow_fallback: bool = True
    timeout: int = 60
    artifact_ids: Optional[List[str]] = None
    session_id: Optional[str] = None

@app.post("/api/orchestrator/execute")
def orchestrator_execute(req: OrchestratorExecuteRequest):
    """
    Execute a task through the orchestrator.
    Enforces strict OPERATIONAL filtering, multimodal capability negotiation,
    workspace validation, and session correlation.
    """
    sess_id = req.session_id or (session_manager.get_current_session().session_id if session_manager.get_current_session() else "default")
    ws_path = Path(req.workspace) if req.workspace else Path(current_config.get("workspace", DEFAULT_WORKSPACE))
    if not ws_path.exists() or not ws_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Dossier workspace introuvable ou inaccessible : {ws_path}")

    # Resolve input artifacts
    loaded_artifacts = []
    if req.artifact_ids:
        for aid in req.artifact_ids:
            a = artifact_manager.get_artifact(aid)
            if a:
                loaded_artifacts.append(a)

    # Attach task to session
    session_manager.attach_task(req.task_id, req.prompt, role=req.role)

    # Convert artifacts to normalized representation
    norm_artifacts_list = []
    for a in loaded_artifacts:
        norm_artifacts_list.append({
            "id": a.id,
            "name": a.name,
            "type": a.source_type.value,
            "path": a.content.binary_path,
            "extracted_text": a.content.extracted_text or a.content.text,
            "pages": a.metadata.pages
        })

    result = agent_orchestrator.execute_task(
        task_id=req.task_id,
        prompt=req.prompt,
        role=req.role,
        workspace=ws_path,
        required_capabilities=req.required_capabilities,
        preferred_agent=req.preferred_agent,
        preferred_provider=req.preferred_provider,
        allow_fallback=req.allow_fallback,
        timeout=req.timeout,
        artifacts=norm_artifacts_list if norm_artifacts_list else None,
        session_id=sess_id
    )
    return result

@app.get("/api/orchestrator/decisions")
def orchestrator_decisions(limit: int = 20):
    """Return the last N orchestrator decision records."""
    decisions_file = DATA_DIR / "orchestrator_decisions.json"
    if not decisions_file.exists():
        return []
    try:
        with open(decisions_file, "r", encoding="utf-8") as f:
            all_decisions = json.load(f)
        return all_decisions[-limit:]
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@app.get("/api/orchestrator/executions")
def orchestrator_executions(limit: int = 20):
    """Return the last N orchestrator execution traces."""
    exec_file = DATA_DIR / "orchestrator_executions.json"
    if not exec_file.exists():
        return []
    try:
        with open(exec_file, "r", encoding="utf-8") as f:
            all_execs = json.load(f)
        return all_execs[-limit:]
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
