"""
Agy Studio v2.6 — Pattern Engine
Detects recurring patterns in tasks, errors, environments, and corrections.
Follows evidence progression: OBSERVED_PATTERN -> SUPPORTED_PATTERN -> ESTABLISHED_PATTERN.
"""

import time
import json
import sqlite3
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional
from .confidence_engine import ConfidenceLevel

class PatternRecord:
    def __init__(
        self,
        pattern_id: Optional[str] = None,
        pattern_type: str = "COMPONENT_BUG",
        signature: str = "",
        description: str = "",
        occurrences: int = 1,
        status: str = "OBSERVED_PATTERN",
        confidence: str = ConfidenceLevel.OBSERVED.value,
        recommended_strategy_id: Optional[str] = None,
        avoid_strategy_id: Optional[str] = None,
        evidence_refs: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.pattern_id = pattern_id or f"PAT-{time.strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        self.pattern_type = pattern_type
        self.signature = signature
        self.description = description
        self.occurrences = occurrences
        self.status = status
        self.confidence = confidence
        self.recommended_strategy_id = recommended_strategy_id
        self.avoid_strategy_id = avoid_strategy_id
        self.evidence_refs = evidence_refs or []
        self.created_at = created_at or now_iso
        self.updated_at = updated_at or now_iso

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "signature": self.signature,
            "description": self.description,
            "occurrences": self.occurrences,
            "status": self.status,
            "confidence": self.confidence,
            "recommended_strategy_id": self.recommended_strategy_id,
            "avoid_strategy_id": self.avoid_strategy_id,
            "evidence_refs": self.evidence_refs,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class PatternEngine:
    """Manages pattern detection, reinforcement, and persistence in SQLite."""

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
                CREATE TABLE IF NOT EXISTS patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT,
                    signature TEXT UNIQUE,
                    description TEXT,
                    occurrences INTEGER,
                    status TEXT,
                    confidence TEXT,
                    recommended_strategy_id TEXT,
                    avoid_strategy_id TEXT,
                    evidence_refs TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

    def register_or_reinforce(
        self,
        pattern_type: str,
        signature: str,
        description: str,
        evidence_ref: str,
        recommended_strategy_id: Optional[str] = None,
        avoid_strategy_id: Optional[str] = None
    ) -> PatternRecord:
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM patterns WHERE signature = ?", (signature,)).fetchone()
            if row:
                occurrences = row["occurrences"] + 1
                ev = json.loads(row["evidence_refs"]) if row["evidence_refs"] else []
                if evidence_ref and evidence_ref not in ev:
                    ev.append(evidence_ref)

                # Progression rule:
                if occurrences >= 3:
                    status = "ESTABLISHED_PATTERN"
                    confidence = ConfidenceLevel.VERIFIED.value
                elif occurrences >= 2:
                    status = "SUPPORTED_PATTERN"
                    confidence = ConfidenceLevel.SUPPORTED.value
                else:
                    status = "OBSERVED_PATTERN"
                    confidence = ConfidenceLevel.OBSERVED.value

                rec_strat = recommended_strategy_id or row["recommended_strategy_id"]
                avoid_strat = avoid_strategy_id or row["avoid_strategy_id"]

                conn.execute("""
                    UPDATE patterns SET
                        occurrences = ?,
                        status = ?,
                        confidence = ?,
                        recommended_strategy_id = ?,
                        avoid_strategy_id = ?,
                        evidence_refs = ?,
                        updated_at = ?
                    WHERE signature = ?
                """, (
                    occurrences, status, confidence, rec_strat, avoid_strat,
                    json.dumps(ev, ensure_ascii=False), now_iso, signature
                ))
                return PatternRecord(
                    pattern_id=row["pattern_id"],
                    pattern_type=row["pattern_type"],
                    signature=signature,
                    description=description or row["description"],
                    occurrences=occurrences,
                    status=status,
                    confidence=confidence,
                    recommended_strategy_id=rec_strat,
                    avoid_strategy_id=avoid_strat,
                    evidence_refs=ev,
                    created_at=row["created_at"],
                    updated_at=now_iso
                )
            else:
                pat = PatternRecord(
                    pattern_type=pattern_type,
                    signature=signature,
                    description=description,
                    occurrences=1,
                    status="OBSERVED_PATTERN",
                    confidence=ConfidenceLevel.OBSERVED.value,
                    recommended_strategy_id=recommended_strategy_id,
                    avoid_strategy_id=avoid_strategy_id,
                    evidence_refs=[evidence_ref] if evidence_ref else []
                )
                conn.execute("""
                    INSERT INTO patterns (
                        pattern_id, pattern_type, signature, description,
                        occurrences, status, confidence, recommended_strategy_id,
                        avoid_strategy_id, evidence_refs, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pat.pattern_id, pat.pattern_type, pat.signature, pat.description,
                    pat.occurrences, pat.status, pat.confidence, pat.recommended_strategy_id,
                    pat.avoid_strategy_id, json.dumps(pat.evidence_refs, ensure_ascii=False),
                    pat.created_at, pat.updated_at
                ))
                return pat

    def find_matching_patterns(self, text: str) -> List[PatternRecord]:
        lower = text.lower()
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM patterns ORDER BY occurrences DESC").fetchall()
            matches = []
            for r in rows:
                sig = r["signature"].lower()
                if sig in lower or any(word in lower for word in sig.split("_") if len(word) > 3):
                    ev = json.loads(r["evidence_refs"]) if r["evidence_refs"] else []
                    matches.append(PatternRecord(
                        pattern_id=r["pattern_id"],
                        pattern_type=r["pattern_type"],
                        signature=r["signature"],
                        description=r["description"],
                        occurrences=r["occurrences"],
                        status=r["status"],
                        confidence=r["confidence"],
                        recommended_strategy_id=r["recommended_strategy_id"],
                        avoid_strategy_id=r["avoid_strategy_id"],
                        evidence_refs=ev,
                        created_at=r["created_at"],
                        updated_at=r["updated_at"]
                    ))
            return matches

    def list_all(self, limit: int = 50) -> List[PatternRecord]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM patterns ORDER BY occurrences DESC LIMIT ?", (limit,)).fetchall()
            results = []
            for r in rows:
                ev = json.loads(r["evidence_refs"]) if r["evidence_refs"] else []
                results.append(PatternRecord(
                    pattern_id=r["pattern_id"],
                    pattern_type=r["pattern_type"],
                    signature=r["signature"],
                    description=r["description"],
                    occurrences=r["occurrences"],
                    status=r["status"],
                    confidence=r["confidence"],
                    recommended_strategy_id=r["recommended_strategy_id"],
                    avoid_strategy_id=r["avoid_strategy_id"],
                    evidence_refs=ev,
                    created_at=r["created_at"],
                    updated_at=r["updated_at"]
                ))
            return results

    def count(self) -> int:
        with self._get_conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
