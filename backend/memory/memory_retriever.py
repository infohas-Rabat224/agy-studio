"""
Agy Studio — Memory Retriever Subsystem
Provides sub-500ms multi-scope retrieval, full-text search, and pre-flight compilation.
"""

import time
from typing import Optional, Dict, Any, List
from .memory_models import (
    MemoryRecord, PreflightResult, MemoryType,
    MemoryScope, MemoryPriority, MemoryConfidence
)
from .memory_store import MemoryStore
from .memory_ranker import MemoryRanker, extract_keywords
from .memory_summarizer import MemorySummarizer

class MemoryRetriever:
    def __init__(self, store: MemoryStore):
        self.store = store

    def preflight_check(
        self,
        task: str,
        workspace: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> PreflightResult:
        """
        Executes pre-flight memory retrieval before agent planning or implementation.
        Retrieves, scores, ranks, and categorizes relevant memories.
        """
        t0 = time.time()
        import os
        derived_project_id = project_id or (os.path.basename(os.path.normpath(workspace)).strip() if workspace else None)
        # Fetch candidate active records
        candidates = self.store.list_memories(
            project_id=derived_project_id,
            session_id=session_id,
            active_only=True
        )

        # Rank candidates
        ranked_pairs = MemoryRanker.rank_records(
            records=candidates,
            task=task,
            workspace=workspace,
            project_id=project_id,
            session_id=session_id,
            top_k=25,
            min_score=15.0
        )
        ranked = [r for r, _ in ranked_pairs]

        corrections: List[MemoryRecord] = []
        rejected: List[MemoryRecord] = []
        constraints: List[MemoryRecord] = []
        accepted: List[MemoryRecord] = []
        lessons: List[MemoryRecord] = []

        for r in ranked:
            if r.type == MemoryType.CORRECTION.value:
                corrections.append(r)
            elif r.type == MemoryType.REJECTED_APPROACH.value:
                rejected.append(r)
            elif r.type in (MemoryType.CONSTRAINT.value, MemoryType.ARCHITECTURAL_RULE.value, MemoryType.REQUIREMENT.value):
                constraints.append(r)
            elif r.type in (MemoryType.ACCEPTED_APPROACH.value, MemoryType.SUCCESS.value):
                accepted.append(r)
            else:
                lessons.append(r)

        risks = MemorySummarizer.identify_potential_risks(task, rejected, constraints)
        context_md = MemorySummarizer.format_preflight_context(
            task=task,
            corrections=corrections,
            rejected=rejected,
            constraints=constraints,
            accepted=accepted,
            lessons=lessons
        )

        duration_ms = (time.time() - t0) * 1000.0

        # Record retrieval audit event
        self.store.record_audit_event(
            event_type="MEMORY_PREFLIGHT_RETRIEVED",
            session_id=session_id,
            reason=f"Preflight retrieval for task: {task[:50]}",
            payload={
                "task": task[:100],
                "duration_ms": duration_ms,
                "corrections_count": len(corrections),
                "rejected_count": len(rejected),
                "constraints_count": len(constraints)
            }
        )

        return PreflightResult(
            task=task,
            has_critical_corrections=any(c.priority == MemoryPriority.CRITICAL.value for c in corrections),
            has_rejected_approaches=len(rejected) > 0,
            corrections=[c.to_dict() for c in corrections],
            rejected_approaches=[r.to_dict() for r in rejected],
            constraints=[k.to_dict() for k in constraints],
            accepted_approaches=[a.to_dict() for a in accepted],
            lessons=[l.to_dict() for l in lessons],
            potential_risks=risks,
            context_injection_markdown=context_md,
            formatted_prompt_block=context_md
        )

    def search_memories(
        self,
        query: str,
        scope: Optional[str] = None,
        mem_type: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Full text and metadata search across all stored memories."""
        all_mems = self.store.list_memories(
            scope=scope,
            mem_type=mem_type,
            project_id=project_id,
            active_only=False
        )
        q_terms = [t.lower() for t in extract_keywords(query)]
        if not q_terms:
            return [m.to_dict() for m in all_mems[:limit]]

        matched = []
        for m in all_mems:
            blob = f"{m.title or ''} {m.content} {m.reason or ''} {m.rejected_approach or ''} {' '.join(m.keywords)}".lower()
            hits = sum(1 for term in q_terms if term in blob)
            if hits > 0:
                matched.append((m, hits))

        matched.sort(key=lambda x: x[1], reverse=True)
        return [m.to_dict() for m, _ in matched[:limit]]
