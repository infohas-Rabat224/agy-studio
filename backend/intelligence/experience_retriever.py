"""
Agy Studio v2.6 — Experience Retriever
Manages and queries real execution experiences persisted in SQLite.
"""

import time
import json
import sqlite3
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional

class ExperienceRecord:
    def __init__(
        self,
        experience_id: Optional[str] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workspace: Optional[str] = None,
        task: str = "",
        task_type: str = "GENERAL_CODING",
        agent_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
        outcome: str = "SUCCESS",
        exit_code: int = 0,
        verification_evidence: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        execution_time_seconds: float = 0.0,
        timestamp: Optional[str] = None
    ):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.experience_id = experience_id or f"EXP-{time.strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        self.session_id = session_id or ""
        self.project_id = project_id or "default"
        self.workspace = workspace or ""
        self.task = task.strip()
        self.task_type = task_type
        self.agent_id = agent_id or "antigravity"
        self.strategy_id = strategy_id or ""
        self.outcome = outcome
        self.exit_code = exit_code
        self.verification_evidence = verification_evidence or {}
        self.error_message = error_message
        self.execution_time_seconds = execution_time_seconds
        self.timestamp = timestamp or now_iso

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "session_id": self.session_id,
            "project_id": self.project_id,
            "workspace": self.workspace,
            "task": self.task,
            "task_type": self.task_type,
            "agent_id": self.agent_id,
            "strategy_id": self.strategy_id,
            "outcome": self.outcome,
            "exit_code": self.exit_code,
            "verification_evidence": self.verification_evidence,
            "error_message": self.error_message,
            "execution_time_seconds": round(self.execution_time_seconds, 2),
            "timestamp": self.timestamp
        }

class ExperienceRetriever:
    """Stores and retrieves historical execution experiences from SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiences (
                    experience_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    project_id TEXT,
                    workspace TEXT,
                    task TEXT,
                    task_type TEXT,
                    agent_id TEXT,
                    strategy_id TEXT,
                    outcome TEXT,
                    exit_code INTEGER,
                    verification_evidence TEXT,
                    error_message TEXT,
                    execution_time_seconds REAL,
                    timestamp TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exp_task_type ON experiences(task_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exp_project ON experiences(project_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exp_outcome ON experiences(outcome)")

    def record_experience(self, exp: ExperienceRecord) -> ExperienceRecord:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO experiences (
                    experience_id, session_id, project_id, workspace,
                    task, task_type, agent_id, strategy_id, outcome,
                    exit_code, verification_evidence, error_message,
                    execution_time_seconds, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                exp.experience_id,
                exp.session_id,
                exp.project_id,
                exp.workspace,
                exp.task,
                exp.task_type,
                exp.agent_id,
                exp.strategy_id,
                exp.outcome,
                exp.exit_code,
                json.dumps(exp.verification_evidence, ensure_ascii=False),
                exp.error_message,
                exp.execution_time_seconds,
                exp.timestamp
            ))
        return exp

    def list_experiences(
        self,
        task_type: Optional[str] = None,
        project_id: Optional[str] = None,
        outcome: Optional[str] = None,
        limit: int = 50
    ) -> List[ExperienceRecord]:
        query = "SELECT * FROM experiences WHERE 1=1"
        params: List[Any] = []
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        if project_id and project_id != "default":
            query += " AND project_id = ?"
            params.append(project_id)
        if outcome:
            query += " AND outcome = ?"
            params.append(outcome)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def search_similar(
        self,
        task_query: str,
        task_type: Optional[str] = None,
        limit: int = 10
    ) -> List[ExperienceRecord]:
        words = [w.lower() for w in task_query.split() if len(w) > 3]
        if not words:
            return self.list_experiences(task_type=task_type, limit=limit)

        clauses = ["LOWER(task) LIKE ?"] * len(words)
        query = f"SELECT * FROM experiences WHERE ({' OR '.join(clauses)})"
        params: List[Any] = [f"%{w}%" for w in words]
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def count(self) -> int:
        with self._get_conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]

    def _row_to_record(self, row: sqlite3.Row) -> ExperienceRecord:
        ev = {}
        try:
            ev = json.loads(row["verification_evidence"]) if row["verification_evidence"] else {}
        except Exception:
            pass
        return ExperienceRecord(
            experience_id=row["experience_id"],
            session_id=row["session_id"],
            project_id=row["project_id"],
            workspace=row["workspace"],
            task=row["task"],
            task_type=row["task_type"],
            agent_id=row["agent_id"],
            strategy_id=row["strategy_id"],
            outcome=row["outcome"],
            exit_code=row["exit_code"],
            verification_evidence=ev,
            error_message=row["error_message"],
            execution_time_seconds=row["execution_time_seconds"],
            timestamp=row["timestamp"]
        )
