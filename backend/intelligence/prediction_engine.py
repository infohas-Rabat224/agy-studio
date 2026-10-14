"""
Agy Studio v2.6 — Prediction Engine
Creates evidence-based predictions for task execution and verifies them post-run.
"""

import time
import json
import sqlite3
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional
from .confidence_engine import ConfidenceLevel

class PredictionRecord:
    def __init__(
        self,
        prediction_id: Optional[str] = None,
        task_id: str = "",
        session_id: str = "",
        expected_outcome: str = "SUCCESS",
        expected_agent: str = "antigravity",
        expected_strategy: Optional[str] = None,
        confidence: str = ConfidenceLevel.SUPPORTED.value,
        rationale: str = "",
        confirmed: Optional[bool] = None,
        actual_outcome: Optional[str] = None,
        created_at: Optional[str] = None
    ):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.prediction_id = prediction_id or f"PRED-{time.strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        self.task_id = task_id
        self.session_id = session_id
        self.expected_outcome = expected_outcome
        self.expected_agent = expected_agent
        self.expected_strategy = expected_strategy
        self.confidence = confidence
        self.rationale = rationale
        self.confirmed = confirmed
        self.actual_outcome = actual_outcome
        self.created_at = created_at or now_iso

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "expected_outcome": self.expected_outcome,
            "expected_agent": self.expected_agent,
            "expected_strategy": self.expected_strategy,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "confirmed": self.confirmed,
            "actual_outcome": self.actual_outcome,
            "created_at": self.created_at
        }

class PredictionEngine:
    """Stores predictions and updates them when actual results arrive."""

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
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id TEXT PRIMARY KEY,
                    task_id TEXT,
                    session_id TEXT,
                    expected_outcome TEXT,
                    expected_agent TEXT,
                    expected_strategy TEXT,
                    confidence TEXT,
                    rationale TEXT,
                    confirmed INTEGER,
                    actual_outcome TEXT,
                    created_at TEXT
                )
            """)

    def create_prediction(
        self,
        task_id: str,
        session_id: str,
        expected_outcome: str,
        expected_agent: str,
        expected_strategy: Optional[str],
        rationale: str,
        confidence: str = ConfidenceLevel.SUPPORTED.value
    ) -> PredictionRecord:
        pred = PredictionRecord(
            task_id=task_id,
            session_id=session_id,
            expected_outcome=expected_outcome,
            expected_agent=expected_agent,
            expected_strategy=expected_strategy,
            confidence=confidence,
            rationale=rationale
        )
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO predictions (
                    prediction_id, task_id, session_id, expected_outcome,
                    expected_agent, expected_strategy, confidence, rationale,
                    confirmed, actual_outcome, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pred.prediction_id, pred.task_id, pred.session_id, pred.expected_outcome,
                pred.expected_agent, pred.expected_strategy, pred.confidence, pred.rationale,
                None, None, pred.created_at
            ))
        return pred

    def verify_prediction(self, task_id: str, actual_outcome: str) -> Optional[PredictionRecord]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM predictions WHERE task_id = ? ORDER BY created_at DESC LIMIT 1", (task_id,)).fetchone()
            if not row:
                return None

            confirmed = (row["expected_outcome"].upper() == actual_outcome.upper())
            conn.execute("""
                UPDATE predictions SET confirmed = ?, actual_outcome = ? WHERE prediction_id = ?
            """, (1 if confirmed else 0, actual_outcome, row["prediction_id"]))

            return PredictionRecord(
                prediction_id=row["prediction_id"],
                task_id=row["task_id"],
                session_id=row["session_id"],
                expected_outcome=row["expected_outcome"],
                expected_agent=row["expected_agent"],
                expected_strategy=row["expected_strategy"],
                confidence=row["confidence"],
                rationale=row["rationale"],
                confirmed=confirmed,
                actual_outcome=actual_outcome,
                created_at=row["created_at"]
            )

    def list_predictions(self, limit: int = 20) -> List[PredictionRecord]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM predictions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [
                PredictionRecord(
                    prediction_id=r["prediction_id"],
                    task_id=r["task_id"],
                    session_id=r["session_id"],
                    expected_outcome=r["expected_outcome"],
                    expected_agent=r["expected_agent"],
                    expected_strategy=r["expected_strategy"],
                    confidence=r["confidence"],
                    rationale=r["rationale"],
                    confirmed=bool(r["confirmed"]) if r["confirmed"] is not None else None,
                    actual_outcome=r["actual_outcome"],
                    created_at=r["created_at"]
                ) for r in rows
            ]
