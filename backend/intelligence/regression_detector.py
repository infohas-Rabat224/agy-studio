"""
Agy Studio v2.6 — Regression Detector
Detects and tracks regressions in previously verified subsystems.
"""

import time
import json
import sqlite3
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional

class RegressionRecord:
    def __init__(
        self,
        regression_id: Optional[str] = None,
        component: str = "",
        feature_name: str = "",
        previously_verified_at: Optional[str] = None,
        broken_at: Optional[str] = None,
        breaking_session_id: Optional[str] = None,
        breaking_task_id: Optional[str] = None,
        evidence: str = "",
        resolved: bool = False,
        resolved_by_strategy_id: Optional[str] = None,
        regression_test_cmd: Optional[str] = None
    ):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.regression_id = regression_id or f"REG-{time.strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        self.component = component
        self.feature_name = feature_name
        self.previously_verified_at = previously_verified_at or now_iso
        self.broken_at = broken_at or now_iso
        self.breaking_session_id = breaking_session_id or ""
        self.breaking_task_id = breaking_task_id or ""
        self.evidence = evidence
        self.resolved = resolved
        self.resolved_by_strategy_id = resolved_by_strategy_id
        self.regression_test_cmd = regression_test_cmd

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regression_id": self.regression_id,
            "component": self.component,
            "feature_name": self.feature_name,
            "previously_verified_at": self.previously_verified_at,
            "broken_at": self.broken_at,
            "breaking_session_id": self.breaking_session_id,
            "breaking_task_id": self.breaking_task_id,
            "evidence": self.evidence,
            "resolved": self.resolved,
            "resolved_by_strategy_id": self.resolved_by_strategy_id,
            "regression_test_cmd": self.regression_test_cmd
        }

class RegressionDetector:
    """Stores regressions and retrieves them for preflight verification."""

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
                CREATE TABLE IF NOT EXISTS regressions (
                    regression_id TEXT PRIMARY KEY,
                    component TEXT,
                    feature_name TEXT,
                    previously_verified_at TEXT,
                    broken_at TEXT,
                    breaking_session_id TEXT,
                    breaking_task_id TEXT,
                    evidence TEXT,
                    resolved INTEGER,
                    resolved_by_strategy_id TEXT,
                    regression_test_cmd TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reg_comp ON regressions(component)")

    def record_regression(self, reg: RegressionRecord) -> RegressionRecord:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO regressions (
                    regression_id, component, feature_name, previously_verified_at,
                    broken_at, breaking_session_id, breaking_task_id, evidence,
                    resolved, resolved_by_strategy_id, regression_test_cmd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reg.regression_id, reg.component, reg.feature_name, reg.previously_verified_at,
                reg.broken_at, reg.breaking_session_id, reg.breaking_task_id, reg.evidence,
                1 if reg.resolved else 0, reg.resolved_by_strategy_id, reg.regression_test_cmd
            ))
        return reg

    def resolve_regression(self, regression_id: str, resolved_by_strategy_id: str) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute("""
                UPDATE regressions SET resolved = 1, resolved_by_strategy_id = ? WHERE regression_id = ?
            """, (resolved_by_strategy_id, regression_id))
            return cur.rowcount > 0

    def get_unresolved_regressions(self, component: Optional[str] = None) -> List[RegressionRecord]:
        with self._get_conn() as conn:
            if component:
                rows = conn.execute(
                    "SELECT * FROM regressions WHERE resolved = 0 AND LOWER(component) = LOWER(?) ORDER BY broken_at DESC",
                    (component.strip(),)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM regressions WHERE resolved = 0 ORDER BY broken_at DESC"
                ).fetchall()
            return [self._row_to_record(r) for r in rows]

    def list_all(self, limit: int = 50) -> List[RegressionRecord]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM regressions ORDER BY broken_at DESC LIMIT ?", (limit,)).fetchall()
            return [self._row_to_record(r) for r in rows]

    def count(self) -> int:
        with self._get_conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM regressions WHERE resolved = 0").fetchone()[0]

    def _row_to_record(self, row: sqlite3.Row) -> RegressionRecord:
        return RegressionRecord(
            regression_id=row["regression_id"],
            component=row["component"],
            feature_name=row["feature_name"],
            previously_verified_at=row["previously_verified_at"],
            broken_at=row["broken_at"],
            breaking_session_id=row["breaking_session_id"],
            breaking_task_id=row["breaking_task_id"],
            evidence=row["evidence"],
            resolved=bool(row["resolved"]),
            resolved_by_strategy_id=row["resolved_by_strategy_id"],
            regression_test_cmd=row["regression_test_cmd"]
        )
