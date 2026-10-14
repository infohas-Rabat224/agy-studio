"""
Agy Studio — Session Identity, Forensic Lineage & Resumable Workspace Subsystem.
Provides persistent, cryptographically strong session identities, pinning, archiving,
non-destructive resume/fork lineage tracking, soft/permanent deletion, and full-text search.
"""

import os
import sys
import time
import json
import uuid
import secrets
import threading
import subprocess
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List

class SessionState(str, Enum):
    CREATED = "CREATED"
    STARTING = "STARTING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    CLOSED = "CLOSED"
    CRASHED = "CRASHED"
    DELETED = "DELETED"

def normalize_project_id(workspace: Optional[str]) -> str:
    if not workspace:
        return "default"
    clean = os.path.basename(os.path.normpath(workspace)).strip()
    return clean if clean else "default"

def derive_meaningful_name(prompt: str) -> str:
    """Derives a concise, clean project/session title from user prompt."""
    if not prompt:
        return ""
    # Strip markdown headers or command prefixes
    clean = re_strip = prompt.strip()
    for prefix in ["/plan ", "/boost ", "/goal ", "/model ", "Implement ", "Fix ", "Create ", "Build "]:
        if clean.lower().startswith(prefix.lower()):
            clean = clean[len(prefix):].strip()
            break
    # Grab first line or sentence up to 50 chars
    first_line = clean.split("\n")[0].split(".")[0].strip()
    if len(first_line) > 80:
        return first_line[:77] + "..."
    return first_line

class SessionRecord:
    def __init__(
        self,
        session_uuid: str,
        session_id: str,
        process_id: int,
        started_at: str,
        application_version: str = "2.5.0",
        status: str = SessionState.ACTIVE.value,
        workspace: Optional[str] = None,
        display_name: Optional[str] = None,
        pinned: bool = False,
        favorite: bool = False,
        archived: bool = False,
        deleted: bool = False,
        deleted_at: Optional[str] = None,
        project_id: Optional[str] = None,
        parent_session_id: Optional[str] = None,
        resume_source_session_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.session_uuid = session_uuid
        self.session_id = session_id
        self.process_id = process_id
        self.started_at = started_at
        self.ended_at: Optional[str] = None
        self.created_at = created_at or started_at
        self.updated_at = updated_at or now_iso
        self.status = status
        self.application_version = application_version
        self.workspace = workspace
        self.project_id = project_id or normalize_project_id(workspace)
        self.display_name = display_name or session_id
        self.pinned = bool(pinned)
        self.favorite = bool(favorite)
        self.archived = bool(archived)
        self.deleted = bool(deleted)
        self.deleted_at = deleted_at
        self.parent_session_id = parent_session_id
        self.resume_source_session_id = resume_source_session_id
        self.last_task: Optional[str] = None
        self.last_execution: Optional[str] = None

        self.tasks: List[Dict[str, Any]] = []
        self.executions: List[Dict[str, Any]] = []
        self.agents: List[str] = []
        self.artifacts: List[Dict[str, Any]] = []
        self.events: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.correlations: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_uuid": self.session_uuid,
            "session_id": self.session_id,
            "display_name": self.display_name,
            "process_id": self.process_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": self.status,
            "pinned": self.pinned,
            "favorite": self.favorite,
            "archived": self.archived,
            "deleted": self.deleted,
            "deleted_at": self.deleted_at,
            "application_version": self.application_version,
            "workspace": self.workspace,
            "project_id": self.project_id,
            "parent_session_id": self.parent_session_id,
            "resume_source_session_id": self.resume_source_session_id,
            "last_task": self.last_task or (self.tasks[-1].get("prompt", "") if self.tasks else None),
            "last_execution": self.last_execution or (self.executions[-1].get("execution_id", "") if self.executions else None),
            "task_count": len(self.tasks),
            "execution_count": len(self.executions),
            "artifact_count": len(self.artifacts),
            "correlation_count": len(self.correlations),
            "tasks": self.tasks,
            "executions": self.executions,
            "agents": list(set(self.agents)),
            "artifacts": self.artifacts,
            "correlations": self.correlations,
            "events": self.events,
            "errors": self.errors,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionRecord":
        rec = cls(
            session_uuid=data.get("session_uuid", str(uuid.uuid4())),
            session_id=data.get("session_id", "AGY-UNKNOWN"),
            process_id=data.get("process_id", 0),
            started_at=data.get("started_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            application_version=data.get("application_version", "2.5.0"),
            status=data.get("status", SessionState.CLOSED.value),
            workspace=data.get("workspace"),
            display_name=data.get("display_name"),
            pinned=data.get("pinned", False),
            favorite=data.get("favorite", False),
            archived=data.get("archived", False),
            deleted=data.get("deleted", False),
            deleted_at=data.get("deleted_at"),
            project_id=data.get("project_id"),
            parent_session_id=data.get("parent_session_id"),
            resume_source_session_id=data.get("resume_source_session_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
        rec.ended_at = data.get("ended_at")
        rec.last_task = data.get("last_task")
        rec.last_execution = data.get("last_execution")
        rec.tasks = data.get("tasks", [])
        rec.executions = data.get("executions", [])
        rec.agents = data.get("agents", [])
        rec.artifacts = data.get("artifacts", [])
        rec.correlations = data.get("correlations", [])
        rec.events = data.get("events", [])
        rec.errors = data.get("errors", [])
        rec.metadata = data.get("metadata", {})
        return rec


class SessionManager:
    """
    Manages session lifecycle, pinning, archiving, non-destructive resume/fork lineage,
    and audit tracking. Guarantees persistence under data/sessions/<session_id>.json.
    """
    _instance: Optional["SessionManager"] = None
    _lock = threading.RLock()

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (Path(__file__).resolve().parent.parent.parent / "data")
        self.sessions_dir = self.data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[SessionRecord] = None
        SessionManager._instance = self

    @classmethod
    def get_instance(cls, data_dir: Optional[Path] = None) -> "SessionManager":
        with cls._lock:
            if cls._instance is None or (data_dir and cls._instance.data_dir != data_dir):
                cls._instance = cls(data_dir=data_dir)
            return cls._instance

    @staticmethod
    def generate_session_id() -> str:
        now = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        token = secrets.token_hex(4).upper()
        return f"AGY-{now}-{token}"

    def is_pid_alive(self, pid: int) -> bool:
        if not pid or pid <= 0:
            return False
        if pid == os.getpid():
            return True
        try:
            if sys.platform == "win32":
                chk = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                return str(pid) in chk.stdout
            else:
                os.kill(pid, 0)
                return True
        except Exception:
            return False

    def recover_previous_sessions(self) -> List[Dict[str, Any]]:
        recovered = []
        if not self.sessions_dir.exists():
            return recovered

        for s_file in self.sessions_dir.glob("AGY-*.json"):
            try:
                with open(s_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                status = data.get("status")
                pid = data.get("process_id", 0)

                if status in (SessionState.ACTIVE.value, SessionState.STARTING.value, SessionState.CREATED.value):
                    if not self.is_pid_alive(pid):
                        data["status"] = SessionState.CRASHED.value
                        data["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        crashed_event = {
                            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                            "session_id": data.get("session_id"),
                            "timestamp": data["ended_at"],
                            "event_type": "SESSION_CRASH_DETECTED",
                            "source": "SessionManager.recovery",
                            "payload": {"reason": "Host process terminated unexpectedly", "observed_dead_pid": pid}
                        }
                        data.setdefault("events", []).append(crashed_event)
                        with open(s_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        recovered.append(data.get("session_id"))
            except Exception:
                pass
        return recovered

    def create_session(
        self,
        workspace: Optional[str] = None,
        display_name: Optional[str] = None,
        parent_session_id: Optional[str] = None,
        resume_source_session_id: Optional[str] = None,
        application_version: str = "2.5.0"
    ) -> SessionRecord:
        session_uuid = str(uuid.uuid4())
        session_id = self.generate_session_id()
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        pid = os.getpid()

        record = SessionRecord(
            session_uuid=session_uuid,
            session_id=session_id,
            process_id=pid,
            started_at=now_iso,
            application_version=application_version,
            status=SessionState.ACTIVE.value,
            workspace=workspace,
            display_name=display_name or session_id,
            parent_session_id=parent_session_id,
            resume_source_session_id=resume_source_session_id
        )

        record.events.append({
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "session_id": session_id,
            "timestamp": now_iso,
            "event_type": "SESSION_CREATED",
            "source": "SessionManager",
            "payload": {
                "session_uuid": session_uuid,
                "process_id": pid,
                "workspace": workspace,
                "parent_session_id": parent_session_id,
                "resume_source_session_id": resume_source_session_id
            }
        })

        with self._lock:
            self.current_session = record
            self.persist_session(record)

        return record

    def get_current_session(self) -> Optional[SessionRecord]:
        with self._lock:
            return self.current_session

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        with self._lock:
            if self.current_session and self.current_session.session_id == session_id:
                return self.current_session

        s_file = self.sessions_dir / f"{session_id}.json"
        if s_file.exists():
            try:
                with open(s_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return SessionRecord.from_dict(data)
            except Exception:
                pass
        return None

    def list_sessions(
        self,
        include_archived: bool = True,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        results = []
        if not self.sessions_dir.exists():
            return results

        for s_file in self.sessions_dir.glob("AGY-*.json"):
            try:
                with open(s_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                is_deleted = bool(data.get("deleted", False))
                is_archived = bool(data.get("archived", False))

                if is_deleted and not include_deleted:
                    continue
                if is_archived and not include_archived and not data.get("pinned", False):
                    continue

                results.append({
                    "session_id": data.get("session_id"),
                    "session_uuid": data.get("session_uuid"),
                    "display_name": data.get("display_name") or data.get("session_id"),
                    "status": data.get("status"),
                    "pinned": bool(data.get("pinned", False)),
                    "favorite": bool(data.get("favorite", False)),
                    "archived": bool(data.get("archived", False)),
                    "deleted": is_deleted,
                    "deleted_at": data.get("deleted_at"),
                    "started_at": data.get("started_at"),
                    "ended_at": data.get("ended_at"),
                    "updated_at": data.get("updated_at") or data.get("started_at"),
                    "workspace": data.get("workspace"),
                    "project_id": data.get("project_id"),
                    "parent_session_id": data.get("parent_session_id"),
                    "resume_source_session_id": data.get("resume_source_session_id"),
                    "last_task": data.get("last_task"),
                    "task_count": len(data.get("tasks", [])),
                    "execution_count": len(data.get("executions", [])),
                    "artifact_count": len(data.get("artifacts", []))
                })
            except Exception:
                pass

        # Sort: Pinned first, then Favorites, then updated_at descending
        results.sort(
            key=lambda x: (
                1 if x.get("pinned") else 0,
                1 if x.get("favorite") else 0,
                x.get("updated_at") or x.get("started_at") or ""
            ),
            reverse=True
        )
        return results

    def favorite_session(self, session_id: str) -> bool:
        with self._lock:
            target = self.get_session(session_id)
            if not target:
                return False
            target.favorite = True
            target.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            target.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": session_id,
                "timestamp": target.updated_at,
                "event_type": "SESSION_FAVORITED",
                "source": "SessionManager",
                "payload": {}
            })
            self.persist_session(target)
            return True

    def unfavorite_session(self, session_id: str) -> bool:
        with self._lock:
            target = self.get_session(session_id)
            if not target:
                return False
            target.favorite = False
            target.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            target.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": session_id,
                "timestamp": target.updated_at,
                "event_type": "SESSION_UNFAVORITED",
                "source": "SessionManager",
                "payload": {}
            })
            self.persist_session(target)
            return True

    def pin_session(self, session_id: str) -> bool:
        with self._lock:
            target = self.get_session(session_id)
            if not target:
                return False
            target.pinned = True
            target.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            target.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": session_id,
                "timestamp": target.updated_at,
                "event_type": "SESSION_PINNED",
                "source": "SessionManager",
                "payload": {}
            })
            self.persist_session(target)
            return True

    def unpin_session(self, session_id: str) -> bool:
        with self._lock:
            target = self.get_session(session_id)
            if not target:
                return False
            target.pinned = False
            target.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            target.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": session_id,
                "timestamp": target.updated_at,
                "event_type": "SESSION_UNPINNED",
                "source": "SessionManager",
                "payload": {}
            })
            self.persist_session(target)
            return True

    def rename_session(self, session_id: str, new_name: str) -> bool:
        new_name = new_name.strip()
        if not new_name:
            return False
        with self._lock:
            target = self.get_session(session_id)
            if not target:
                return False
            old_name = target.display_name
            target.display_name = new_name
            target.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            target.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": session_id,
                "timestamp": target.updated_at,
                "event_type": "SESSION_RENAMED",
                "source": "SessionManager",
                "payload": {"old_name": old_name, "new_name": new_name}
            })
            self.persist_session(target)
            return True

    def archive_session(self, session_id: str) -> bool:
        with self._lock:
            target = self.get_session(session_id)
            if not target:
                return False
            target.archived = True
            target.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            target.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": session_id,
                "timestamp": target.updated_at,
                "event_type": "SESSION_ARCHIVED",
                "source": "SessionManager",
                "payload": {}
            })
            self.persist_session(target)
            return True

    def restore_session(self, session_id: str) -> bool:
        with self._lock:
            target = self.get_session(session_id)
            if not target:
                return False
            target.archived = False
            target.deleted = False
            target.deleted_at = None
            target.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            target.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": session_id,
                "timestamp": target.updated_at,
                "event_type": "SESSION_RESTORED",
                "source": "SessionManager",
                "payload": {}
            })
            self.persist_session(target)
            return True

    def delete_session(self, session_id: str) -> bool:
        """Soft delete to recoverable trash."""
        with self._lock:
            target = self.get_session(session_id)
            if not target:
                return False
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            target.deleted = True
            target.deleted_at = now_iso
            target.status = SessionState.DELETED.value
            target.updated_at = now_iso
            target.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": session_id,
                "timestamp": now_iso,
                "event_type": "SESSION_DELETED",
                "source": "SessionManager",
                "payload": {"soft_delete": True}
            })
            self.persist_session(target)
            return True

    def delete_permanently(self, session_id: str) -> Tuple[bool, str]:
        """
        Permanently destroys session record and forensic file.
        Enforces rule: Pinned sessions MUST be unpinned before permanent deletion!
        Uses session_uuid as immutable anchor.
        """
        with self._lock:
            target = self.get_session(session_id)
            if not target:
                return False, "Session not found."
            if target.pinned:
                return False, "Pinned sessions cannot be deleted. Please unpin first."

            s_file = self.sessions_dir / f"{target.session_id}.json"
            try:
                if s_file.exists():
                    s_file.unlink()
                if self.current_session and self.current_session.session_id == target.session_id:
                    self.current_session = None
                return True, f"Session {session_id} ({target.session_uuid}) permanently deleted."
            except Exception as e:
                return False, str(e)

    def resume_session(self, source_session_id: str) -> SessionRecord:
        """
        Non-destructive Resume:
        Creates a BRAND NEW runtime session with parent/source pointers,
        preserving historical forensic integrity of the old session.
        """
        with self._lock:
            source = self.get_session(source_session_id)
            if not source:
                raise ValueError(f"Historical session '{source_session_id}' not found.")

            # New runtime session
            display_name = source.display_name or source.session_id
            if not display_name.endswith("(Resumed)"):
                display_name = f"{display_name} (Resumed)"

            new_sess = self.create_session(
                workspace=source.workspace,
                display_name=display_name,
                parent_session_id=source.session_id,
                resume_source_session_id=source.session_id
            )

            # Record RESUME lineage event in both sessions
            resume_evt = {
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": new_sess.session_id,
                "timestamp": new_sess.started_at,
                "event_type": "SESSION_RESUMED",
                "source": "SessionManager",
                "payload": {
                    "source_session_id": source.session_id,
                    "source_session_uuid": source.session_uuid,
                    "source_task_count": len(source.tasks),
                    "source_artifact_count": len(source.artifacts)
                }
            }
            new_sess.events.append(resume_evt)
            self.persist_session(new_sess)

            source.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": source.session_id,
                "timestamp": new_sess.started_at,
                "event_type": "SESSION_RESUMED_CHILD_SPAWNED",
                "source": "SessionManager",
                "payload": {"child_session_id": new_sess.session_id}
            })
            self.persist_session(source)

            return new_sess

    def fork_session(self, source_session_id: str, fork_name: Optional[str] = None) -> SessionRecord:
        """
        Forks a session into an isolated branch for safe experimentation.
        """
        with self._lock:
            source = self.get_session(source_session_id)
            if not source:
                raise ValueError(f"Source session '{source_session_id}' not found.")

            name = fork_name or f"{source.display_name} (Fork)"
            new_sess = self.create_session(
                workspace=source.workspace,
                display_name=name,
                parent_session_id=source.session_id
            )

            fork_evt = {
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": new_sess.session_id,
                "timestamp": new_sess.started_at,
                "event_type": "SESSION_FORKED",
                "source": "SessionManager",
                "payload": {
                    "parent_session_id": source.session_id,
                    "parent_session_uuid": source.session_uuid
                }
            }
            new_sess.events.append(fork_evt)
            self.persist_session(new_sess)

            source.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": source.session_id,
                "timestamp": new_sess.started_at,
                "event_type": "SESSION_FORKED_CHILD_SPAWNED",
                "source": "SessionManager",
                "payload": {"fork_session_id": new_sess.session_id}
            })
            self.persist_session(source)

            return new_sess

    def get_session_lineage(self, session_id: str) -> Dict[str, Any]:
        """Constructs full lineage tree (ancestors, descendants, forks, resumes)."""
        target = self.get_session(session_id)
        if not target:
            return {"error": "Session not found", "session_id": session_id}

        all_sessions = self.list_sessions(include_archived=True, include_deleted=True)

        # Ancestry chain
        ancestors = []
        curr_parent = target.parent_session_id
        while curr_parent:
            p_rec = next((s for s in all_sessions if s["session_id"] == curr_parent), None)
            if p_rec:
                ancestors.append(p_rec)
                curr_parent = p_rec.get("parent_session_id")
            else:
                break

        # Descendants
        children = [s for s in all_sessions if s.get("parent_session_id") == session_id]

        return {
            "session_id": target.session_id,
            "session_uuid": target.session_uuid,
            "display_name": target.display_name,
            "parent_session_id": target.parent_session_id,
            "resume_source_session_id": target.resume_source_session_id,
            "ancestors": ancestors,
            "children": children
        }

    def search_sessions(
        self,
        query: str,
        include_archived: bool = True,
        include_deleted: bool = False,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Full text and metadata search across all stored sessions."""
        q = query.lower().strip()
        all_s = self.list_sessions(include_archived=include_archived, include_deleted=include_deleted)
        if not q:
            return all_s[:limit]

        matched = []
        for s in all_s:
            full = self.get_session(s["session_id"])
            if not full:
                continue

            # Build searchable text blob
            tasks_text = " ".join([t.get("prompt", "") for t in full.tasks])
            artifacts_text = " ".join([a.get("name", "") for a in full.artifacts])
            errors_text = " ".join([e.get("message", "") for e in full.errors])
            blob = f"{full.display_name} {full.session_id} {full.workspace or ''} {tasks_text} {artifacts_text} {errors_text}".lower()

            if q in blob:
                s_copy = dict(s)
                s_copy["match_preview"] = (
                    tasks_text[:100] if q in tasks_text.lower() else
                    artifacts_text[:100] if q in artifacts_text.lower() else
                    full.display_name
                )
                matched.append(s_copy)

        return matched[:limit]

    def close_session(self, reason: str = "normal_shutdown") -> bool:
        with self._lock:
            if not self.current_session:
                return False
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self.current_session.status = SessionState.CLOSED.value
            self.current_session.ended_at = now_iso
            self.current_session.updated_at = now_iso
            self.current_session.events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": self.current_session.session_id,
                "timestamp": now_iso,
                "event_type": "SESSION_CLOSED",
                "source": "SessionManager",
                "payload": {"reason": reason}
            })
            self.persist_session(self.current_session)
            return True

    def persist_session(self, session: Optional[SessionRecord] = None):
        target = session or self.current_session
        if not target:
            return
        s_file = self.sessions_dir / f"{target.session_id}.json"
        try:
            with open(s_file, "w", encoding="utf-8") as f:
                json.dump(target.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add_event(self, event_type: str, source: str, payload: Any) -> Optional[Dict[str, Any]]:
        with self._lock:
            if not self.current_session:
                return None
            evt = {
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": self.current_session.session_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "event_type": event_type,
                "source": source,
                "payload": payload
            }
            self.current_session.events.append(evt)
            self.current_session.updated_at = evt["timestamp"]
            self.persist_session(self.current_session)
            return evt

    def attach_task(
        self,
        task_id: str,
        prompt: str,
        role: str = "CODER",
        status: str = "CREATED",
        metadata: Optional[Dict[str, Any]] = None
    ):
        with self._lock:
            if not self.current_session:
                return
            entry = {
                "task_id": task_id,
                "session_id": self.current_session.session_id,
                "role": role,
                "prompt": prompt[:300] if prompt else "",
                "status": status,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "metadata": metadata or {}
            }
            self.current_session.tasks.append(entry)
            self.current_session.last_task = prompt[:100] if prompt else task_id
            self.current_session.updated_at = entry["created_at"]

            # Auto-assign meaningful display name if currently unnamed or raw session ID
            if (
                not self.current_session.display_name or
                self.current_session.display_name.startswith("AGY-") or
                self.current_session.display_name in ["New Session", "Untitled", "Session 123"]
            ):
                candidate_name = derive_meaningful_name(prompt)
                if candidate_name:
                    self.current_session.display_name = candidate_name

            self.add_event("TASK_CREATED", "Orchestrator", {"task_id": task_id, "role": role})

    def attach_execution(
        self,
        execution_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        workspace: Optional[str] = None,
        status: str = "COMPLETED",
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
        duration_ms: int = 0,
        exit_code: int = 0,
        artifacts: Optional[List[str]] = None,
        **kwargs
    ):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        exec_id = execution_id or f"exec_{uuid.uuid4().hex[:8]}"
        t_id = task_id or kwargs.get("command", "task")
        a_id = agent_id or kwargs.get("agent_name", "runtime")
        ws = workspace or (self.current_session.workspace if self.current_session else "")
        ret_code = exit_code if exit_code is not None else kwargs.get("return_code", 0)
        art_ids = artifacts or kwargs.get("artifact_ids", [])

        with self._lock:
            if not self.current_session:
                return
            entry = {
                "execution_id": exec_id,
                "session_id": self.current_session.session_id,
                "task_id": t_id,
                "agent_id": a_id,
                "agent_name": a_id,
                "workspace": ws,
                "status": status,
                "started_at": started_at or now_iso,
                "ended_at": ended_at or now_iso,
                "duration_ms": duration_ms,
                "exit_code": ret_code,
                "artifacts": art_ids
            }
            self.current_session.executions.append(entry)
            self.current_session.last_execution = exec_id
            self.current_session.updated_at = entry["ended_at"]
            if a_id not in self.current_session.agents:
                self.current_session.agents.append(a_id)
            self.add_event("TASK_EXECUTED", "AgentRuntime", {
                "execution_id": exec_id,
                "agent_id": a_id,
                "exit_code": ret_code,
                "status": status
            })

    def attach_artifact(
        self,
        artifact_id: str,
        name: str,
        artifact_type: str = "unknown",
        size_bytes: int = 0,
        source: str = "upload",
        path: str = "",
        sha256: str = ""
    ):
        with self._lock:
            if not self.current_session:
                return
            entry = {
                "artifact_id": artifact_id,
                "session_id": self.current_session.session_id,
                "name": name,
                "type": artifact_type,
                "source": source,
                "path": path,
                "sha256": sha256,
                "size_bytes": size_bytes,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            self.current_session.artifacts.append(entry)
            self.current_session.updated_at = entry["created_at"]
            self.add_event("ARTIFACT_ATTACHED", "ArtifactManager", {
                "artifact_id": artifact_id,
                "name": name,
                "type": artifact_type
            })

    def attach_error(self, message: str, component: str, trace: Optional[str] = None):
        with self._lock:
            if not self.current_session:
                return
            err = {
                "error_id": f"err_{uuid.uuid4().hex[:8]}",
                "session_id": self.current_session.session_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "message": message,
                "component": component,
                "trace": trace
            }
            self.current_session.errors.append(err)
            self.current_session.updated_at = err["timestamp"]
            self.persist_session(self.current_session)

    def set_session_workspace(self, workspace_path: str):
        with self._lock:
            if not self.current_session:
                return
            self.current_session.workspace = workspace_path
            self.current_session.project_id = normalize_project_id(workspace_path)
            self.current_session.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self.add_event("WORKSPACE_CHANGED", "WorkspaceManager", {"workspace": workspace_path})

    def record_correlation(
        self,
        task_id: Optional[str] = None,
        artifact_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        result: str = "SUCCESS",
        reason: Optional[str] = None,
        details: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        with self._lock:
            target_session = self.get_session(session_id) if session_id else self.current_session
            if not target_session:
                target_session = self.current_session
            corr = {
                "correlation_id": f"CORR-{secrets.token_hex(4).upper()}",
                "session_id": target_session.session_id if target_session else "",
                "session_uuid": target_session.session_uuid if target_session else "",
                "task_id": task_id or "",
                "artifact_id": artifact_id or "",
                "execution_id": execution_id or "",
                "agent_id": agent_id or "",
                "provider_id": provider_id or "",
                "capabilities": capabilities or [],
                "result": result,
                "reason": reason or "",
                "details": details or "",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            if kwargs:
                for k, v in kwargs.items():
                    if k not in corr:
                        corr[k] = v
            if target_session:
                target_session.correlations.append(corr)
                self.persist_session(target_session)
            return corr

    def get_correlations(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if session_id:
                s = self.get_session(session_id)
                return s.correlations if s else []
            all_c = []
            seen_ids = set()
            if self.current_session:
                for c in self.current_session.correlations:
                    all_c.append(c)
                    seen_ids.add(c.get("correlation_id"))
            for s_info in self.list_sessions(include_archived=True, include_deleted=True):
                s = self.get_session(s_info["session_id"])
                if s:
                    for c in s.correlations:
                        cid = c.get("correlation_id")
                        if cid not in seen_ids:
                            all_c.append(c)
                            seen_ids.add(cid)
            return all_c

    def find_correlations_by_artifact(self, artifact_id: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        corrs = self.get_correlations(session_id)
        return [c for c in corrs if c.get("artifact_id") == artifact_id]

    def find_correlations_by_task(self, task_id: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        corrs = self.get_correlations(session_id)
        return [c for c in corrs if c.get("task_id") == task_id]

    def find_correlations_by_execution(self, execution_id: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        corrs = self.get_correlations(session_id)
        return [c for c in corrs if c.get("execution_id") == execution_id]

