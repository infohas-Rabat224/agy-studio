"""
Agy Studio v2.6 — Strategy Engine
Learns and recommends proven execution strategies.
Penalizes failed strategies and integrates with Anti-Repetition Guard.
"""

import time
import json
import sqlite3
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional
from .confidence_engine import ConfidenceEngine, ConfidenceLevel

class StrategyRecord:
    def __init__(
        self,
        strategy_id: Optional[str] = None,
        name: str = "",
        task_type: str = "GENERAL_CODING",
        description: str = "",
        recommended_agent: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        verification_plan: Optional[List[str]] = None,
        success_count: int = 0,
        failure_count: int = 0,
        confidence: str = ConfidenceLevel.OBSERVED.value,
        status: str = "ACTIVE",  # ACTIVE, REJECTED, SUPERSEDED
        rejection_reason: Optional[str] = None,
        replacement_strategy_id: Optional[str] = None,
        project_id: Optional[str] = None,
        evidence_refs: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.strategy_id = strategy_id or f"STRAT-{time.strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        self.name = name.strip()
        self.task_type = task_type
        self.description = description.strip()
        self.recommended_agent = recommended_agent
        self.dependencies = dependencies or []
        self.verification_plan = verification_plan or []
        self.success_count = success_count
        self.failure_count = failure_count
        self.confidence = confidence
        self.status = status
        self.rejection_reason = rejection_reason
        self.replacement_strategy_id = replacement_strategy_id
        self.project_id = project_id
        self.evidence_refs = evidence_refs or []
        self.created_at = created_at or now_iso
        self.updated_at = updated_at or now_iso

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "task_type": self.task_type,
            "description": self.description,
            "recommended_agent": self.recommended_agent,
            "dependencies": self.dependencies,
            "verification_plan": self.verification_plan,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "confidence": self.confidence,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "replacement_strategy_id": self.replacement_strategy_id,
            "project_id": self.project_id,
            "evidence_refs": self.evidence_refs,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class StrategyEngine:
    """Manages active, successful, and rejected strategies in SQLite."""

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
                CREATE TABLE IF NOT EXISTS strategies (
                    strategy_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE,
                    task_type TEXT,
                    description TEXT,
                    recommended_agent TEXT,
                    dependencies TEXT,
                    verification_plan TEXT,
                    success_count INTEGER,
                    failure_count INTEGER,
                    confidence TEXT,
                    status TEXT,
                    rejection_reason TEXT,
                    replacement_strategy_id TEXT,
                    project_id TEXT,
                    evidence_refs TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_task_type ON strategies(task_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_status ON strategies(status)")

    def save_or_update(self, strat: StrategyRecord) -> StrategyRecord:
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        strat.updated_at = now_iso
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO strategies (
                    strategy_id, name, task_type, description, recommended_agent,
                    dependencies, verification_plan, success_count, failure_count,
                    confidence, status, rejection_reason, replacement_strategy_id,
                    project_id, evidence_refs, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                strat.strategy_id, strat.name, strat.task_type, strat.description,
                strat.recommended_agent, json.dumps(strat.dependencies, ensure_ascii=False),
                json.dumps(strat.verification_plan, ensure_ascii=False), strat.success_count,
                strat.failure_count, strat.confidence, strat.status, strat.rejection_reason,
                strat.replacement_strategy_id, strat.project_id,
                json.dumps(strat.evidence_refs, ensure_ascii=False),
                strat.created_at, strat.updated_at
            ))
        return strat

    def get_strategy_by_id(self, strategy_id: str) -> Optional[StrategyRecord]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM strategies WHERE strategy_id = ?", (strategy_id,)).fetchone()
            return self._row_to_record(row) if row else None

    def get_strategy_by_name(self, name: str) -> Optional[StrategyRecord]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM strategies WHERE LOWER(name) = LOWER(?)", (name.strip(),)).fetchone()
            return self._row_to_record(row) if row else None

    def record_success(self, strategy_id_or_name: str, evidence_ref: str, agent_id: Optional[str] = None) -> Optional[StrategyRecord]:
        strat = self.get_strategy_by_id(strategy_id_or_name) or self.get_strategy_by_name(strategy_id_or_name)
        if not strat:
            return None

        strat.success_count += 1
        if evidence_ref and evidence_ref not in strat.evidence_refs:
            strat.evidence_refs.append(evidence_ref)
        if agent_id:
            strat.recommended_agent = agent_id

        # Confidence progression on success
        if strat.success_count >= 3:
            strat.confidence = ConfidenceLevel.VERIFIED.value
        elif strat.success_count >= 1 and ConfidenceEngine.get_rank(strat.confidence) < 3:
            strat.confidence = ConfidenceLevel.SUPPORTED.value

        return self.save_or_update(strat)

    def record_failure(self, strategy_id_or_name: str, error_message: str, evidence_ref: str) -> Optional[StrategyRecord]:
        strat = self.get_strategy_by_id(strategy_id_or_name) or self.get_strategy_by_name(strategy_id_or_name)
        if not strat:
            return None

        strat.failure_count += 1
        if evidence_ref and evidence_ref not in strat.evidence_refs:
            strat.evidence_refs.append(evidence_ref)

        # Failure decreases confidence
        strat.confidence = ConfidenceEngine.demote_on_conflict(strat.confidence, error_message)
        return self.save_or_update(strat)

    def mark_rejected(
        self,
        strategy_id_or_name: str,
        reason: str,
        replacement_strategy_id: Optional[str] = None
    ) -> Optional[StrategyRecord]:
        strat = self.get_strategy_by_id(strategy_id_or_name) or self.get_strategy_by_name(strategy_id_or_name)
        if not strat:
            # Create a rejected strategy entry if not existing
            strat = StrategyRecord(
                name=strategy_id_or_name,
                description=f"Rejected strategy: {strategy_id_or_name}",
                status="REJECTED",
                confidence=ConfidenceLevel.USER_CONFIRMED.value,
                rejection_reason=reason,
                replacement_strategy_id=replacement_strategy_id
            )
        else:
            strat.status = "REJECTED"
            strat.rejection_reason = reason
            strat.replacement_strategy_id = replacement_strategy_id

        return self.save_or_update(strat)

    def recommend_strategy(self, task_type: str, keywords: Optional[List[str]] = None) -> Optional[StrategyRecord]:
        """Finds the highest confidence active strategy for a task type and keywords."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM strategies
                WHERE status = 'ACTIVE' AND task_type = ?
            """, (task_type,)).fetchall()

            if not rows:
                return None

            records = [self._row_to_record(r) for r in rows]
            if not keywords:
                records.sort(key=lambda s: (s.success_count, s.updated_at), reverse=True)
                return records[0]

            def score_strat(s: StrategyRecord) -> float:
                score = float(s.success_count * 2.0)
                name_lower = s.name.lower()
                desc_lower = s.description.lower()
                for kw in keywords:
                    clean_kw = kw.strip().lower()
                    if len(clean_kw) > 2:
                        if clean_kw in name_lower:
                            score += 15.0
                        elif clean_kw in desc_lower:
                            score += 5.0
                return score

            records.sort(key=score_strat, reverse=True)
            return records[0]

    def list_strategies(self, status: Optional[str] = None, limit: int = 50) -> List[StrategyRecord]:
        with self._get_conn() as conn:
            query = "SELECT * FROM strategies WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY success_count DESC, updated_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def count(self) -> int:
        with self._get_conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM strategies").fetchone()[0]

    def _row_to_record(self, row: sqlite3.Row) -> StrategyRecord:
        deps = []
        plan = []
        ev = []
        try:
            deps = json.loads(row["dependencies"]) if row["dependencies"] else []
            plan = json.loads(row["verification_plan"]) if row["verification_plan"] else []
            ev = json.loads(row["evidence_refs"]) if row["evidence_refs"] else []
        except Exception:
            pass

        return StrategyRecord(
            strategy_id=row["strategy_id"],
            name=row["name"],
            task_type=row["task_type"],
            description=row["description"],
            recommended_agent=row["recommended_agent"],
            dependencies=deps,
            verification_plan=plan,
            success_count=row["success_count"],
            failure_count=row["failure_count"],
            confidence=row["confidence"],
            status=row["status"],
            rejection_reason=row["rejection_reason"],
            replacement_strategy_id=row["replacement_strategy_id"],
            project_id=row["project_id"],
            evidence_refs=ev,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
