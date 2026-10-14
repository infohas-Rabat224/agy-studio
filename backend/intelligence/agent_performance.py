"""
Agy Studio v2.6 — Agent Performance Engine
Maintains empirical performance metrics per agent and task type.
Provides real explainability data for agent selection.
"""

import time
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional

class AgentPerformanceRecord:
    def __init__(
        self,
        agent_id: str,
        task_type: str,
        total_runs: int = 0,
        success_runs: int = 0,
        failed_runs: int = 0,
        verified_runs: int = 0,
        regression_runs: int = 0,
        avg_duration_seconds: float = 0.0,
        last_run_at: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.task_type = task_type
        self.total_runs = total_runs
        self.success_runs = success_runs
        self.failed_runs = failed_runs
        self.verified_runs = verified_runs
        self.regression_runs = regression_runs
        self.avg_duration_seconds = avg_duration_seconds
        self.last_run_at = last_run_at

    @property
    def success_rate(self) -> float:
        return (self.success_runs / self.total_runs) if self.total_runs > 0 else 0.0

    @property
    def verification_rate(self) -> float:
        return (self.verified_runs / self.total_runs) if self.total_runs > 0 else 0.0

    @property
    def regression_rate(self) -> float:
        return (self.regression_runs / self.total_runs) if self.total_runs > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "total_runs": self.total_runs,
            "success_runs": self.success_runs,
            "failed_runs": self.failed_runs,
            "verified_runs": self.verified_runs,
            "regression_runs": self.regression_runs,
            "success_rate": round(self.success_rate, 2),
            "verification_rate": round(self.verification_rate, 2),
            "regression_rate": round(self.regression_rate, 2),
            "avg_duration_seconds": round(self.avg_duration_seconds, 2),
            "last_run_at": self.last_run_at
        }

class AgentPerformanceEngine:
    """Calculates and stores empirical performance of agents by task category."""

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
                CREATE TABLE IF NOT EXISTS agent_performance (
                    agent_id TEXT,
                    task_type TEXT,
                    total_runs INTEGER,
                    success_runs INTEGER,
                    failed_runs INTEGER,
                    verified_runs INTEGER,
                    regression_runs INTEGER,
                    avg_duration_seconds REAL,
                    last_run_at TEXT,
                    PRIMARY KEY (agent_id, task_type)
                )
            """)

    def record_run(
        self,
        agent_id: str,
        task_type: str,
        success: bool,
        verified: bool = False,
        is_regression: bool = False,
        duration_seconds: float = 0.0
    ):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM agent_performance WHERE agent_id = ? AND task_type = ?",
                (agent_id, task_type)
            ).fetchone()

            if row:
                total = row["total_runs"] + 1
                succ = row["success_runs"] + (1 if success else 0)
                fail = row["failed_runs"] + (0 if success else 1)
                veri = row["verified_runs"] + (1 if verified else 0)
                regr = row["regression_runs"] + (1 if is_regression else 0)
                prev_avg = row["avg_duration_seconds"] or 0.0
                new_avg = ((prev_avg * row["total_runs"]) + duration_seconds) / total

                conn.execute("""
                    UPDATE agent_performance SET
                        total_runs = ?, success_runs = ?, failed_runs = ?,
                        verified_runs = ?, regression_runs = ?, avg_duration_seconds = ?,
                        last_run_at = ?
                    WHERE agent_id = ? AND task_type = ?
                """, (total, succ, fail, veri, regr, new_avg, now_iso, agent_id, task_type))
            else:
                conn.execute("""
                    INSERT INTO agent_performance (
                        agent_id, task_type, total_runs, success_runs, failed_runs,
                        verified_runs, regression_runs, avg_duration_seconds, last_run_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent_id, task_type, 1,
                    1 if success else 0,
                    0 if success else 1,
                    1 if verified else 0,
                    1 if is_regression else 0,
                    duration_seconds, now_iso
                ))

    def get_performance(self, agent_id: str, task_type: str) -> Optional[AgentPerformanceRecord]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM agent_performance WHERE agent_id = ? AND task_type = ?",
                (agent_id, task_type)
            ).fetchone()
            if not row:
                return None
            return AgentPerformanceRecord(
                agent_id=row["agent_id"],
                task_type=row["task_type"],
                total_runs=row["total_runs"],
                success_runs=row["success_runs"],
                failed_runs=row["failed_runs"],
                verified_runs=row["verified_runs"],
                regression_runs=row["regression_runs"],
                avg_duration_seconds=row["avg_duration_seconds"],
                last_run_at=row["last_run_at"]
            )

    def explain_selection(self, agent_id: str, task_type: str) -> List[str]:
        """Explains why an agent is recommended or scored favorably based on real data."""
        perf = self.get_performance(agent_id, task_type)
        points = []
        if not perf or perf.total_runs == 0:
            points.append(f"• Baseline compatibility: registered for '{task_type}'")
            points.append("• No prior negative regressions recorded")
            return points

        points.append(f"• {perf.success_runs}/{perf.total_runs} related tasks successful ({int(perf.success_rate * 100)}%)")
        if perf.verified_runs > 0:
            points.append(f"• {perf.verified_runs} tasks backed by hard verification evidence")
        if perf.regression_runs == 0:
            points.append("• Zero unresolved critical regressions")
        else:
            points.append(f"• ⚠ {perf.regression_runs} historical regressions noted")
        if perf.avg_duration_seconds > 0:
            points.append(f"• Average verified response time: {round(perf.avg_duration_seconds, 1)}s")

        return points

    def list_all_performance(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM agent_performance ORDER BY total_runs DESC").fetchall()
            return [
                AgentPerformanceRecord(
                    agent_id=r["agent_id"],
                    task_type=r["task_type"],
                    total_runs=r["total_runs"],
                    success_runs=r["success_runs"],
                    failed_runs=r["failed_runs"],
                    verified_runs=r["verified_runs"],
                    regression_runs=r["regression_runs"],
                    avg_duration_seconds=r["avg_duration_seconds"],
                    last_run_at=r["last_run_at"]
                ).to_dict() for r in rows
            ]
