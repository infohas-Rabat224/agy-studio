"""
Agy Studio — Anti-Repetition Guard Subsystem
Intercepts proposed plans, code solutions, and commands before execution to verify
they do not regress into previously rejected approaches.
"""

import re
from typing import Optional, Dict, Any, List
from .memory_models import (
    MemoryRecord, GuardResult, MemoryType,
    MemoryPriority, MemoryConfidence
)
from .memory_store import MemoryStore
from .memory_ranker import extract_keywords

class MemoryGuard:
    def __init__(self, store: MemoryStore):
        self.store = store

    def check_proposal(
        self,
        proposal: str,
        workspace: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        allow_reconsideration: bool = False
    ) -> GuardResult:
        """
        Verifies if the proposed implementation matches a previously rejected approach.
        Returns GuardResult detailing whether it is blocked, reason, and accepted alternatives.
        """
        if not proposal or allow_reconsideration:
            return GuardResult(allowed=True, violation=False)

        # Check for explicit user reconsideration override
        p_lower = proposal.lower()
        if any(override in p_lower for override in [
            "reconsider the previous approach",
            "reconsidérer l'approche précédente",
            "force previously rejected",
            "override memory guard"
        ]):
            return GuardResult(allowed=True, violation=False)

        # Load all active rejected approach records
        rejected_records = self.store.list_memories(
            mem_type=MemoryType.REJECTED_APPROACH.value,
            project_id=project_id,
            active_only=True
        )

        prop_keywords = set(extract_keywords(proposal))

        for rec in rejected_records:
            target_pattern = (rec.rejected_approach or rec.content).lower()
            pattern_keywords = set(extract_keywords(target_pattern))

            # Direct substring match
            is_match = False
            if target_pattern in p_lower:
                is_match = True
            elif len(pattern_keywords) >= 2 and len(prop_keywords.intersection(pattern_keywords)) >= len(pattern_keywords):
                # All key terms of the rejected approach are present in the proposal
                is_match = True

            if is_match:
                warn_msg = (
                    f"⚠️ PREVIOUSLY REJECTED APPROACH DETECTED: '{rec.rejected_approach or rec.content}'.\n"
                    f"REASON: {rec.reason or 'Explicitly rejected by user.'}\n"
                )
                if rec.accepted_alternative:
                    warn_msg += f"PREFERRED ACCEPTED ALTERNATIVE: '{rec.accepted_alternative}'.\n"
                warn_msg += "Do not reintroduce this solution unless explicitly authorized with 'Reconsider the previous approach'."

                # Record guard violation audit event
                self.store.record_audit_event(
                    event_type="GUARD_VIOLATION_BLOCKED",
                    memory_id=rec.memory_id,
                    session_id=session_id,
                    source="MemoryGuard",
                    reason=f"Blocked reintroduction of rejected approach: {rec.rejected_approach or rec.content}",
                    payload={"proposal": proposal[:200], "rejected_pattern": target_pattern}
                )

                return GuardResult(
                    allowed=False,
                    violation=True,
                    warning=warn_msg,
                    rejected_pattern=rec.rejected_approach or rec.content,
                    reason=rec.reason,
                    accepted_alternative=rec.accepted_alternative,
                    evidence_session_id=rec.session_id
                )

        return GuardResult(allowed=True, violation=False)
