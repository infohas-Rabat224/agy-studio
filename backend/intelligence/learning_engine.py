"""
Agy Studio v2.6 — Learning Engine
Central orchestrator for evidence-based learning, corrections, promotions, and forensic events.
"""

import time
import json
import sqlite3
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional
from .confidence_engine import ConfidenceLevel, ConfidenceEngine
from .strategy_engine import StrategyEngine, StrategyRecord
from .experience_retriever import ExperienceRetriever, ExperienceRecord
from .pattern_engine import PatternEngine
from .agent_performance import AgentPerformanceEngine
from .regression_detector import RegressionDetector, RegressionRecord
from .knowledge_engine import KnowledgeEngine

class ForensicEvent:
    def __init__(
        self,
        event_type: str,
        session_id: str = "",
        project_id: str = "default",
        task_id: str = "",
        source: str = "INTELLIGENCE",
        evidence_refs: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ):
        self.event_id = f"EVT-{time.strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        self.event_type = event_type
        self.session_id = session_id
        self.project_id = project_id
        self.task_id = task_id
        self.source = source
        self.evidence_refs = evidence_refs or []
        self.details = details or {}
        self.timestamp = timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "session_id": self.session_id,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "source": self.source,
            "evidence_refs": self.evidence_refs,
            "details": self.details,
            "timestamp": self.timestamp
        }

class LearningEngine:
    """Orchestrates learning from experience, outcomes, corrections, and emits forensic events."""

    def __init__(
        self,
        db_path: Path,
        strategy_engine: StrategyEngine,
        experience_retriever: ExperienceRetriever,
        pattern_engine: PatternEngine,
        agent_performance: AgentPerformanceEngine,
        regression_detector: RegressionDetector,
        knowledge_engine: KnowledgeEngine
    ):
        self.db_path = db_path
        self.strategy_engine = strategy_engine
        self.experience_retriever = experience_retriever
        self.pattern_engine = pattern_engine
        self.agent_performance = agent_performance
        self.regression_detector = regression_detector
        self.knowledge_engine = knowledge_engine
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT,
                    session_id TEXT,
                    project_id TEXT,
                    task_id TEXT,
                    source TEXT,
                    evidence_refs TEXT,
                    details TEXT,
                    timestamp TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_le_type ON learning_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_le_sess ON learning_events(session_id)")

    def emit_event(
        self,
        event_type: str,
        session_id: str = "",
        project_id: str = "default",
        task_id: str = "",
        source: str = "INTELLIGENCE",
        evidence_refs: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ForensicEvent:
        evt = ForensicEvent(
            event_type=event_type,
            session_id=session_id,
            project_id=project_id,
            task_id=task_id,
            source=source,
            evidence_refs=evidence_refs,
            details=details
        )
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO learning_events (
                    event_id, event_type, session_id, project_id, task_id,
                    source, evidence_refs, details, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evt.event_id, evt.event_type, evt.session_id, evt.project_id,
                evt.task_id, evt.source, json.dumps(evt.evidence_refs, ensure_ascii=False),
                json.dumps(evt.details, ensure_ascii=False), evt.timestamp
            ))
        return evt

    def learn_user_correction(
        self,
        rejected_entity: str,
        accepted_alternative: Optional[str] = None,
        reason: str = "User explicit rejection",
        session_id: str = "",
        project_id: str = "default",
        task_id: str = ""
    ) -> Dict[str, Any]:
        """Learns directly from user correction (Highest Authority: USER_CONFIRMED)."""
        # Mark strategy rejected if matches
        rej_strat = self.strategy_engine.mark_rejected(
            strategy_id_or_name=rejected_entity,
            reason=reason,
            replacement_strategy_id=accepted_alternative
        )

        # Knowledge entity and relation
        e_rej = self.knowledge_engine.add_entity("Strategy", rejected_entity, {"status": "REJECTED"}, ConfidenceLevel.USER_CONFIRMED.value)
        if accepted_alternative:
            e_acc = self.knowledge_engine.add_entity("Strategy", accepted_alternative, {"status": "ACCEPTED"}, ConfidenceLevel.USER_CONFIRMED.value)
            self.knowledge_engine.add_relation(e_rej.entity_id, "SUPERSEDES", e_acc.entity_id, weight=2.0)

        # Emit forensic event
        evt = self.emit_event(
            event_type="LEARNING_CONFIRMED",
            session_id=session_id,
            project_id=project_id,
            task_id=task_id,
            source="USER_CORRECTION",
            details={
                "rejected": rejected_entity,
                "accepted": accepted_alternative,
                "reason": reason,
                "confidence": ConfidenceLevel.USER_CONFIRMED.value
            }
        )

        return {
            "status": "learned",
            "confidence": ConfidenceLevel.USER_CONFIRMED.value,
            "rejected_strategy": rej_strat.to_dict() if rej_strat else None,
            "event_id": evt.event_id
        }

    def learn_outcome(
        self,
        task: str,
        task_type: str,
        agent_id: str,
        strategy_name: Optional[str],
        success: bool,
        verified: bool,
        evidence_type: str,
        evidence_details: Dict[str, Any],
        exit_code: int = 0,
        error_message: Optional[str] = None,
        execution_time_seconds: float = 0.0,
        session_id: str = "",
        project_id: str = "default",
        workspace: str = "",
        task_id: str = ""
    ) -> ExperienceRecord:
        """Synthesizes outcome into experience, agent performance, strategy, and forensic events."""
        outcome_str = "SUCCESS" if success else "FAILURE"

        # 1. Record experience
        exp = ExperienceRecord(
            session_id=session_id,
            project_id=project_id,
            workspace=workspace,
            task=task,
            task_type=task_type,
            agent_id=agent_id,
            strategy_id=strategy_name or "",
            outcome=outcome_str,
            exit_code=exit_code,
            verification_evidence={"type": evidence_type, "details": evidence_details},
            error_message=error_message,
            execution_time_seconds=execution_time_seconds
        )
        self.experience_retriever.record_experience(exp)

        # 2. Update agent performance
        self.agent_performance.record_run(
            agent_id=agent_id,
            task_type=task_type,
            success=success,
            verified=verified,
            duration_seconds=execution_time_seconds
        )
        self.emit_event(
            event_type="AGENT_PERFORMANCE_UPDATED",
            session_id=session_id,
            project_id=project_id,
            task_id=task_id,
            evidence_refs=[exp.experience_id],
            details={"agent_id": agent_id, "success": success, "verified": verified}
        )

        # 3. Strategy reinforcement or penalty
        if strategy_name:
            if success and verified:
                self.strategy_engine.record_success(strategy_name, evidence_ref=exp.experience_id, agent_id=agent_id)
                self.emit_event(
                    event_type="STRATEGY_REUSED" if "reused" in task.lower() else "LEARNING_CONFIRMED",
                    session_id=session_id,
                    project_id=project_id,
                    task_id=task_id,
                    evidence_refs=[exp.experience_id],
                    details={"strategy": strategy_name, "status": "reinforced"}
                )
            elif not success:
                self.strategy_engine.record_failure(strategy_name, error_message or "Execution failed", evidence_ref=exp.experience_id)

        # 4. Pattern detection
        if not success and error_message:
            sig = f"ERR_{task_type}_{abs(hash(error_message[:40]))}"
            self.pattern_engine.register_or_reinforce(
                pattern_type="COMPONENT_BUG",
                signature=sig,
                description=error_message[:100],
                evidence_ref=exp.experience_id,
                avoid_strategy_id=strategy_name
            )
            self.emit_event(
                event_type="PATTERN_DETECTED",
                session_id=session_id,
                project_id=project_id,
                task_id=task_id,
                evidence_refs=[exp.experience_id],
                details={"pattern": sig}
            )

        # 5. Emit OUTCOME_ANALYZED
        self.emit_event(
            event_type="OUTCOME_ANALYZED",
            session_id=session_id,
            project_id=project_id,
            task_id=task_id,
            evidence_refs=[exp.experience_id],
            details={
                "outcome": outcome_str,
                "verified": verified,
                "evidence_type": evidence_type
            }
        )

        return exp

    def list_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM learning_events ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            results = []
            for r in rows:
                ev = json.loads(r["evidence_refs"]) if r["evidence_refs"] else []
                det = json.loads(r["details"]) if r["details"] else {}
                results.append({
                    "event_id": r["event_id"],
                    "event_type": r["event_type"],
                    "session_id": r["session_id"],
                    "project_id": r["project_id"],
                    "task_id": r["task_id"],
                    "source": r["source"],
                    "evidence_refs": ev,
                    "details": det,
                    "timestamp": r["timestamp"]
                })
            return results

    def count_events(self) -> int:
        with self._get_conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0]
