"""
Agy Studio — Automated Memory Learning & Extraction Subsystem
Extracts grounded, factual memory records from real user corrections, rejected approaches,
execution outcomes, and explicit user commands. No hallucinations, no fake memories.
"""

import os
import re
from typing import Optional, Dict, Any, List, Tuple
from .memory_models import (
    MemoryRecord, MemoryType, MemoryScope,
    MemoryPriority, MemoryConfidence
)
from .memory_store import MemoryStore

class MemoryLearner:
    def __init__(self, store: MemoryStore):
        self.store = store

    def process_user_input(
        self,
        user_text: str,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workspace: Optional[str] = None
    ) -> List[MemoryRecord]:
        """
        Analyzes user message for explicit corrections, rejections, architectural rules,
        or 'Remember that...' directives.
        """
        if not user_text:
            return []

        if not project_id and workspace:
            norm_ws = os.path.normpath(workspace)
            base = os.path.basename(norm_ws)
            project_id = base if base else norm_ws

        created_memories = []
        u_text = user_text.strip()

        # 1. Check for "Remember that..." or "Rappelle-toi que..."
        remember_match = re.search(r'(?i)(?:remember that|n\'oublie pas que|retiens que|rappelle-toi que)\s+(.+)', u_text)
        if remember_match:
            rule_content = remember_match.group(1).strip()
            scope = MemoryScope.GLOBAL.value if any(k in rule_content.lower() for k in ["always", "never", "jamais", "toujours"]) else MemoryScope.PROJECT.value
            rec = MemoryRecord(
                scope=scope,
                type=MemoryType.ARCHITECTURAL_RULE.value,
                content=rule_content,
                title="Règle explicite utilisateur",
                source="USER",
                confidence=MemoryConfidence.USER_CONFIRMED.value,
                priority=MemoryPriority.CRITICAL.value,
                session_id=session_id,
                project_id=project_id,
                workspace=workspace
            )
            self.store.save_memory(rec, audit_reason="Extracted from user directive ('Remember that...')")
            created_memories.append(rec)

        # 2. Check for direct rule or correction starting with "Never ...", "Always ...", "Ne jamais ..."
        directive_match = re.search(r'(?i)^(?:never|always|ne jamais|toujours)\s+(.+)', u_text)
        if directive_match and not remember_match:
            rule_content = u_text.strip()
            scope = MemoryScope.GLOBAL.value
            rec = MemoryRecord(
                scope=scope,
                type=MemoryType.CORRECTION.value,
                content=rule_content,
                title="Consigne de comportement stricte",
                source="USER",
                confidence=MemoryConfidence.USER_CONFIRMED.value,
                priority=MemoryPriority.CRITICAL.value,
                session_id=session_id,
                project_id=project_id,
                workspace=workspace
            )
            self.store.save_memory(rec, audit_reason="Extracted from direct user policy ('Never/Always...')")
            created_memories.append(rec)

        # 3. Check for explicit rejection / "Do not use..." / "Ne pas utiliser..."
        rejection_match = re.search(
            r'(?i)(?:do not use|don\'t use|never use|ne pas utiliser|n\'utilise pas|rejette|reject)\s+([^.]+?)(?:\s+(?:because|car|puisque|it causes|parce que)\s+([^.]+))?(?:\.|$)',
            u_text
        )
        if rejection_match:
            rejected_item = rejection_match.group(1).strip()
            reason = rejection_match.group(2).strip() if rejection_match.group(2) else "Explicitly rejected by user"
            
            # Look for alternative in text AFTER the rejection sentence
            remainder = u_text[rejection_match.end():].strip()
            alternative = None
            if remainder:
                alt_match = re.search(r'(?i)(?:(?:use|utilise|utiliser)\s+([^.]+?)(?:\s+instead|\s+à la place|\.|$))', remainder)
                if alt_match:
                    alternative = alt_match.group(1).strip()
            if not alternative:
                alt_match2 = re.search(r'(?i)(?:instead use|à la place)\s+([^.]+)', u_text)
                if alt_match2:
                    alternative = alt_match2.group(1).strip()

            rec = MemoryRecord(
                scope=MemoryScope.PROJECT.value,
                type=MemoryType.REJECTED_APPROACH.value,
                content=f"Rejected approach: {rejected_item}. Reason: {reason}",
                title=f"Approche Rejetée: {rejected_item[:40]}",
                reason=reason,
                rejected_approach=rejected_item,
                accepted_alternative=alternative,
                source="USER",
                confidence=MemoryConfidence.USER_CONFIRMED.value,
                priority=MemoryPriority.CRITICAL.value,
                session_id=session_id,
                project_id=project_id,
                workspace=workspace
            )
            self.store.save_memory(rec, audit_reason="Extracted from explicit user rejection")
            created_memories.append(rec)

            # Also create an explicit CORRECTION record
            corr_rec = MemoryRecord(
                scope=MemoryScope.PROJECT.value,
                type=MemoryType.CORRECTION.value,
                content=f"Do not use {rejected_item}. {reason}",
                title=f"Correction: {rejected_item[:40]}",
                source="USER",
                confidence=MemoryConfidence.USER_CONFIRMED.value,
                priority=MemoryPriority.CRITICAL.value,
                session_id=session_id,
                project_id=project_id,
                workspace=workspace
            )
            self.store.save_memory(corr_rec, audit_reason="User correction created alongside rejected approach")
            created_memories.append(corr_rec)

        return created_memories

    def record_execution_outcome(
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
        """
        Records verified execution outcomes (ACCEPTED_APPROACH or LESSON/FAILURE).
        """
        if not project_id and workspace:
            norm_ws = os.path.normpath(workspace)
            base = os.path.basename(norm_ws)
            project_id = base if base else norm_ws

        if success and approach_summary:
            rec = MemoryRecord(
                scope=MemoryScope.PROJECT.value,
                type=MemoryType.ACCEPTED_APPROACH.value,
                content=approach_summary,
                title=f"Solution Validée: {approach_summary[:40]}",
                source="EXECUTION",
                confidence=MemoryConfidence.VERIFIED.value,
                priority=MemoryPriority.HIGH.value,
                accepted_alternative=approach_summary,
                session_id=session_id,
                project_id=project_id,
                workspace=workspace,
                evidence_refs=[evidence_ref] if evidence_ref else []
            )
            self.store.save_memory(rec, audit_reason="Verified execution success recorded")
            return rec
        elif not success and error_message:
            rec = MemoryRecord(
                scope=MemoryScope.PROJECT.value,
                type=MemoryType.FAILURE.value,
                content=f"Task '{task[:50]}' failed with exit code {exit_code}: {error_message[:200]}",
                title=f"Échec Exécution: {task[:40]}",
                reason=error_message[:200],
                source="EXECUTION",
                confidence=MemoryConfidence.OBSERVED.value,
                priority=MemoryPriority.MEDIUM.value,
                session_id=session_id,
                project_id=project_id,
                workspace=workspace,
                evidence_refs=[evidence_ref] if evidence_ref else []
            )
            self.store.save_memory(rec, audit_reason="Execution failure recorded")
            return rec
        return None
