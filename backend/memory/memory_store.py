"""
Agy Studio — Persistent Learning Memory Store
Combines an indexed SQLite database for < 5ms queries with partitioned JSON mirrors:
data/memory/global.json, corrections.json, decisions.json, constraints.json, lessons.json, projects/, sessions/.
Includes secret redaction, audit logging, and deterministic conflict resolution.
"""

import os
import re
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from .memory_models import (
    MemoryRecord, MemoryScope, MemoryType,
    MemoryConfidence, MemoryPriority
)

SECRET_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|secret|token|password|auth|bearer)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{8,})["\']?'), r'\1: [REDACTED_SECRET]'),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'ghp_[a-zA-Z0-9]{20,}'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'ey[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}'), '[REDACTED_JWT_TOKEN]'),
]

def sanitize_text(text: str) -> str:
    """Removes sensitive credentials, API keys, passwords from memory content."""
    if not text:
        return ""
    sanitized = text
    for pattern, repl in SECRET_PATTERNS:
        sanitized = pattern.sub(repl, sanitized)
    return sanitized

class MemoryStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.memory_dir = self.data_dir / "memory"
        self.projects_dir = self.memory_dir / "projects"
        self.sessions_dir = self.memory_dir / "sessions"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.memory_dir / "memory.db"
        self.audit_log_path = self.memory_dir / "audit_events.json"
        self._lock = threading.RLock()
        self._init_db()
        self._sync_all_json_mirrors()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    reason TEXT,
                    source TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    session_id TEXT,
                    project_id TEXT,
                    workspace TEXT,
                    keywords_json TEXT,
                    evidence_json TEXT,
                    rejected_approach TEXT,
                    accepted_alternative TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    superseded_by TEXT,
                    metadata_json TEXT
                )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_scope ON memories(scope)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_proj ON memories(project_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_sess ON memories(session_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_active ON memories(active)")

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    memory_id TEXT,
                    session_id TEXT,
                    source TEXT NOT NULL,
                    reason TEXT,
                    payload_json TEXT
                )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_evt_mem ON memory_events(memory_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_evt_sess ON memory_events(session_id)")
                conn.commit()

    def record_audit_event(
        self,
        event_type: str,
        memory_id: Optional[str] = None,
        session_id: Optional[str] = None,
        source: str = "SYSTEM",
        reason: str = "",
        payload: Optional[Dict[str, Any]] = None
    ):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        event_id = f"aud_{uuid.uuid4().hex[:10]}"
        evt = {
            "event_id": event_id,
            "timestamp": now_iso,
            "event_type": event_type,
            "memory_id": memory_id,
            "session_id": session_id,
            "source": source,
            "reason": reason,
            "payload": payload or {}
        }
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.cursor().execute("""
                    INSERT INTO memory_events (event_id, timestamp, event_type, memory_id, session_id, source, reason, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (event_id, now_iso, event_type, memory_id, session_id, source, reason, json.dumps(payload or {})))
                    conn.commit()
            except Exception:
                pass

            # Also append to audit_events.json mirror
            try:
                events = []
                if self.audit_log_path.exists():
                    try:
                        with open(self.audit_log_path, "r", encoding="utf-8") as f:
                            events = json.load(f)
                    except Exception:
                        events = []
                events.append(evt)
                if len(events) > 500:
                    events = events[-500:] # Retain recent 500 audit events in JSON mirror
                with open(self.audit_log_path, "w", encoding="utf-8") as f:
                    json.dump(events, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    def save_memory(self, record: MemoryRecord, audit_reason: str = "Created memory record") -> MemoryRecord:
        record.content = sanitize_text(record.content)
        if record.title:
            record.title = sanitize_text(record.title)
        if record.reason:
            record.reason = sanitize_text(record.reason)
        if record.rejected_approach:
            record.rejected_approach = sanitize_text(record.rejected_approach)
        if record.accepted_alternative:
            record.accepted_alternative = sanitize_text(record.accepted_alternative)

        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        record.updated_at = now_iso

        with self._lock:
            # Check for conflicting or identical memory
            existing = self._find_conflict(record)
            if existing and existing.memory_id != record.memory_id:
                # Resolve conflict deterministically
                self._resolve_conflict(existing, record)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT OR REPLACE INTO memories (
                    memory_id, scope, type, title, content, reason, source,
                    confidence, priority, created_at, updated_at, session_id,
                    project_id, workspace, keywords_json, evidence_json,
                    rejected_approach, accepted_alternative, active, superseded_by,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.memory_id, record.scope, record.type, record.title,
                    record.content, record.reason, record.source, record.confidence,
                    record.priority, record.created_at, record.updated_at,
                    record.session_id, record.project_id, record.workspace,
                    json.dumps(record.keywords or []), json.dumps(record.evidence_refs or []),
                    record.rejected_approach, record.accepted_alternative,
                    1 if record.active else 0, record.superseded_by,
                    json.dumps(record.metadata or {})
                ))
                conn.commit()

            self.record_audit_event(
                event_type="MEMORY_SAVED",
                memory_id=record.memory_id,
                session_id=record.session_id,
                source=record.source,
                reason=audit_reason,
                payload={"scope": record.scope, "type": record.type, "priority": record.priority}
            )

            self._sync_all_json_mirrors()
        return record

    def get_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM memories WHERE memory_id = ?", (memory_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_record(row)
        return None

    def list_memories(
        self,
        scope: Optional[str] = None,
        mem_type: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[MemoryRecord]:
        query = "SELECT * FROM memories WHERE 1=1"
        params = []
        if active_only:
            query += " AND active = 1"
        if mem_type:
            query += " AND type = ?"
            params.append(mem_type)

        if scope:
            query += " AND scope = ?"
            params.append(scope)
            if project_id and scope == MemoryScope.PROJECT.value:
                query += " AND (project_id = ? OR project_id IS NULL)"
                params.append(project_id)
            if session_id and scope == MemoryScope.SESSION.value:
                query += " AND session_id = ?"
                params.append(session_id)
        elif project_id or session_id:
            # Contextual multi-tier retrieval: GLOBAL + Matching PROJECT + Matching SESSION
            conditions = ["scope = 'GLOBAL'"]
            if project_id:
                conditions.append("(scope = 'PROJECT' AND (project_id = ? OR project_id IS NULL))")
                params.append(project_id)
            else:
                conditions.append("scope = 'PROJECT'")
            if session_id:
                conditions.append("(scope = 'SESSION' AND session_id = ?)")
                params.append(session_id)
            query += f" AND ({' OR '.join(conditions)})"

        query += " ORDER BY CASE priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, created_at DESC"

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()
                return [self._row_to_record(r) for r in rows]

    def confirm_memory(self, memory_id: str, new_scope: Optional[str] = None, new_priority: Optional[str] = None) -> Optional[MemoryRecord]:
        rec = self.get_memory(memory_id)
        if not rec:
            return None
        rec.confidence = MemoryConfidence.USER_CONFIRMED.value
        if new_scope:
            rec.scope = new_scope
        if new_priority:
            rec.priority = new_priority
        rec.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.save_memory(rec, audit_reason="User confirmed memory")
        self.record_audit_event("MEMORY_CONFIRMED", memory_id=memory_id, source="USER", reason="User confirmation")
        return rec

    def supersede_memory(self, old_memory_id: str, new_memory_id: str, reason: str = "") -> bool:
        old_rec = self.get_memory(old_memory_id)
        if not old_rec:
            return False
        old_rec.active = False
        old_rec.superseded_by = new_memory_id
        old_rec.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.save_memory(old_rec, audit_reason=f"Superseded by {new_memory_id}: {reason}")
        self.record_audit_event("MEMORY_SUPERSEDED", memory_id=old_memory_id, reason=f"Superseded by {new_memory_id}")
        return True

    def deactivate_memory(self, memory_id: str, reason: str = "User deactivated") -> bool:
        rec = self.get_memory(memory_id)
        if not rec:
            return False
        rec.active = False
        rec.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.save_memory(rec, audit_reason=reason)
        self.record_audit_event("MEMORY_DEACTIVATED", memory_id=memory_id, source="USER", reason=reason)
        return True

    def _find_conflict(self, new_record: MemoryRecord) -> Optional[MemoryRecord]:
        """Finds if a similar active memory exists for the same scope/project."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check for exact duplicate or direct contradiction
            cursor.execute("""
            SELECT * FROM memories 
            WHERE active = 1 AND memory_id != ? 
            AND type = ? AND scope = ?
            """, (new_record.memory_id, new_record.type, new_record.scope))
            rows = cursor.fetchall()
            for r in rows:
                existing = self._row_to_record(r)
                if existing.content.lower().strip() == new_record.content.lower().strip():
                    return existing
                if existing.rejected_approach and new_record.rejected_approach:
                    if existing.rejected_approach.lower() == new_record.rejected_approach.lower():
                        return existing
        return None

    def _resolve_conflict(self, existing: MemoryRecord, new_record: MemoryRecord):
        """
        Deterministic conflict resolution:
        USER_CONFIRMED > VERIFIED > OBSERVED > UNVERIFIED.
        If both same, recency wins (new supersedes old).
        Old is marked superseded_by, active = False.
        """
        conf_rank = {
            MemoryConfidence.USER_CONFIRMED.value: 4,
            MemoryConfidence.VERIFIED.value: 3,
            MemoryConfidence.OBSERVED.value: 2,
            MemoryConfidence.UNVERIFIED.value: 1
        }
        old_rank = conf_rank.get(existing.confidence, 1)
        new_rank = conf_rank.get(new_record.confidence, 1)

        if new_rank >= old_rank:
            existing.active = False
            existing.superseded_by = new_record.memory_id
            self.save_memory(existing, audit_reason=f"Superseded by higher confidence/newer {new_record.memory_id}")
            self.record_audit_event("MEMORY_SUPERSEDED", memory_id=existing.memory_id, reason="Conflict resolution")

    def _row_to_record(self, r: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            memory_id=r["memory_id"],
            scope=r["scope"],
            type=r["type"],
            title=r["title"],
            content=r["content"],
            reason=r["reason"],
            source=r["source"],
            confidence=r["confidence"],
            priority=r["priority"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            session_id=r["session_id"],
            project_id=r["project_id"],
            workspace=r["workspace"],
            keywords=json.loads(r["keywords_json"] or "[]"),
            evidence_refs=json.loads(r["evidence_json"] or "[]"),
            rejected_approach=r["rejected_approach"],
            accepted_alternative=r["accepted_alternative"],
            active=bool(r["active"]),
            superseded_by=r["superseded_by"],
            metadata=json.loads(r["metadata_json"] or "{}")
        )

    def _sync_all_json_mirrors(self):
        """Synchronizes SQL database into clean partitioned JSON files for human auditability."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM memories WHERE active = 1")
                active_records = [self._row_to_record(r).to_dict() for r in cursor.fetchall()]

            # Partition
            global_mems = [m for m in active_records if m["scope"] == MemoryScope.GLOBAL.value]
            corrections = [m for m in active_records if m["type"] in (MemoryType.CORRECTION.value, MemoryType.REJECTED_APPROACH.value)]
            decisions = [m for m in active_records if m["type"] == MemoryType.DECISION.value]
            constraints = [m for m in active_records if m["type"] in (MemoryType.CONSTRAINT.value, MemoryType.ARCHITECTURAL_RULE.value)]
            lessons = [m for m in active_records if m["type"] in (MemoryType.LESSON.value, MemoryType.SUCCESS.value, MemoryType.FAILURE.value, MemoryType.ACCEPTED_APPROACH.value)]

            with open(self.memory_dir / "global.json", "w", encoding="utf-8") as f:
                json.dump(global_mems, f, indent=2, ensure_ascii=False)
            with open(self.memory_dir / "corrections.json", "w", encoding="utf-8") as f:
                json.dump(corrections, f, indent=2, ensure_ascii=False)
            with open(self.memory_dir / "decisions.json", "w", encoding="utf-8") as f:
                json.dump(decisions, f, indent=2, ensure_ascii=False)
            with open(self.memory_dir / "constraints.json", "w", encoding="utf-8") as f:
                json.dump(constraints, f, indent=2, ensure_ascii=False)
            with open(self.memory_dir / "lessons.json", "w", encoding="utf-8") as f:
                json.dump(lessons, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
