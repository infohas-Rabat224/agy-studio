"""
Agy Studio — Central Memory Manager
Coordinates store, retriever, guard, learner, and migration of legacy memory.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from .memory_models import (
    MemoryRecord, PreflightResult, GuardResult,
    MemoryCreateRequest, MemoryConfirmRequest, MemorySupersedeRequest,
    MemoryScope, MemoryType, MemoryPriority, MemoryConfidence
)
from .memory_store import MemoryStore
from .memory_retriever import MemoryRetriever
from .memory_guard import MemoryGuard
from .memory_learning import MemoryLearner

class MemoryManager:
    _instance: Optional["MemoryManager"] = None

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.store = MemoryStore(data_dir)
        self.retriever = MemoryRetriever(self.store)
        self.guard = MemoryGuard(self.store)
        self.learner = MemoryLearner(self.store)
        self._migrate_legacy_if_needed()

    @classmethod
    def get_instance(cls, data_dir: Optional[Path] = None) -> "MemoryManager":
        if cls._instance is None:
            if not data_dir:
                data_dir = Path(__file__).resolve().parent.parent.parent / "data"
            cls._instance = cls(data_dir)
        return cls._instance

    def preflight_check(
        self,
        task: str,
        workspace: Optional[str] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> PreflightResult:
        return self.retriever.preflight_check(
            task=task,
            workspace=workspace,
            project_id=project_id,
            session_id=session_id,
            agent_id=agent_id
        )

    def check_guard(
        self,
        proposal: str,
        workspace: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        allow_reconsideration: bool = False
    ) -> GuardResult:
        return self.guard.check_proposal(
            proposal=proposal,
            workspace=workspace,
            project_id=project_id,
            session_id=session_id,
            allow_reconsideration=allow_reconsideration
        )

    def learn_from_user(
        self,
        user_text: str,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workspace: Optional[str] = None
    ) -> List[MemoryRecord]:
        return self.learner.process_user_input(
            user_text=user_text,
            session_id=session_id,
            project_id=project_id,
            workspace=workspace
        )

    def record_outcome(
        self,
        task: str,
        approach_summary: str,
        success: bool,
        exit_code: int = 0,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workspace: Optional[str] = None,
        evidence_ref: Optional[str] = None
    ) -> Optional[MemoryRecord]:
        return self.learner.record_execution_outcome(
            task=task,
            approach_summary=approach_summary,
            success=success,
            exit_code=exit_code,
            error_message=error_message,
            session_id=session_id,
            project_id=project_id,
            workspace=workspace,
            evidence_ref=evidence_ref
        )

    def create_memory(self, req: MemoryCreateRequest) -> MemoryRecord:
        rec = MemoryRecord(
            scope=req.scope,
            type=req.type,
            content=req.content,
            title=req.title,
            reason=req.reason,
            source=req.source,
            confidence=req.confidence,
            priority=req.priority,
            session_id=req.session_id,
            project_id=req.project_id,
            workspace=req.workspace,
            keywords=req.keywords or [],
            evidence_refs=req.evidence_refs or [],
            rejected_approach=req.rejected_approach,
            accepted_alternative=req.accepted_alternative
        )
        return self.store.save_memory(rec, audit_reason="Explicit API memory creation")

    def get_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        return self.store.get_memory(memory_id)

    def list_memories(
        self,
        scope: Optional[str] = None,
        mem_type: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        recs = self.store.list_memories(
            scope=scope,
            mem_type=mem_type,
            project_id=project_id,
            session_id=session_id,
            active_only=active_only
        )
        return [r.to_dict() for r in recs]

    def confirm_memory(self, memory_id: str, new_scope: Optional[str] = None, new_priority: Optional[str] = None) -> Optional[Dict[str, Any]]:
        rec = self.store.confirm_memory(memory_id, new_scope=new_scope, new_priority=new_priority)
        return rec.to_dict() if rec else None

    def supersede_memory(self, old_memory_id: str, new_memory_id: str, reason: str = "") -> bool:
        return self.store.supersede_memory(old_memory_id, new_memory_id, reason=reason)

    def deactivate_memory(self, memory_id: str, reason: str = "User deactivated") -> bool:
        return self.store.deactivate_memory(memory_id, reason=reason)

    def search_memories(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self.retriever.search_memories(query=query, limit=limit)

    def _migrate_legacy_if_needed(self):
        """Safely imports existing data/memory.json into indexed store if DB is empty."""
        try:
            existing = self.store.list_memories(active_only=False)
            if existing:
                return # Already initialized

            legacy_file = self.data_dir / "memory.json"
            if not legacy_file.exists():
                return

            import json
            with open(legacy_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            categories = data.get("categories", {})
            for cat_name, items in categories.items():
                for item in items:
                    content = item.get("content", "")
                    title = item.get("title", "")
                    tag = item.get("tag", "")

                    m_type = MemoryType.CONSTRAINT.value
                    priority = MemoryPriority.MEDIUM.value
                    if tag == "CRITIQUE":
                        priority = MemoryPriority.CRITICAL.value
                        m_type = MemoryType.ARCHITECTURAL_RULE.value
                    elif "Règles" in cat_name:
                        m_type = MemoryType.ARCHITECTURAL_RULE.value

                    rec = MemoryRecord(
                        scope=MemoryScope.GLOBAL.value,
                        type=m_type,
                        title=title,
                        content=content,
                        source="SYSTEM",
                        confidence=MemoryConfidence.USER_CONFIRMED.value,
                        priority=priority
                    )
                    self.store.save_memory(rec, audit_reason="Migrated from legacy memory.json")
        except Exception:
            pass
