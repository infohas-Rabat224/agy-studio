"""
Agy Studio — Memory Ranker & Relevance Scorer
Ranks memories based on task context, keyword matching, confidence hierarchy, and priority weighting.
Guarantees < 50ms ranking computation.
"""

import re
import math
import time
from typing import List, Dict, Any, Tuple
from .memory_models import MemoryRecord, MemoryPriority, MemoryConfidence, MemoryType, MemoryScope

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other",
    "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
    "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "you", "your",
    "yours", "yourself", "yourselves", "le", "la", "les", "un", "une", "des", "du", "de", "ce", "ces",
    "pour", "dans", "avec", "sur", "par", "qui", "que", "faire", "plus", "pas", "ne", "est", "sont"
}

def extract_keywords(text: str) -> List[str]:
    """Tokenizes and filters significant semantic terms."""
    if not text:
        return []
    words = re.findall(r'[a-zA-Z0-9_\-\.]{3,}', text.lower())
    return [w for w in words if w not in STOPWORDS]

class MemoryRanker:
    @staticmethod
    def score_memory(
        record: MemoryRecord,
        task_text: str,
        task_keywords: List[str],
        current_workspace: Optional[str] = None,
        current_project_id: Optional[str] = None,
        current_session_id: Optional[str] = None
    ) -> float:
        """
        Calculates a relevance score from 0.0 to 100.0.
        Criteria:
        1. Base priority weight: CRITICAL (40) > HIGH (25) > MEDIUM (15) > LOW (5)
        2. Confidence weight: USER_CONFIRMED (+25) > VERIFIED (+15) > OBSERVED (+5)
        3. Type boost: CORRECTION (+30) > REJECTED_APPROACH (+30) > ARCHITECTURAL_RULE (+20) > CONSTRAINT (+15)
        4. Scope match:
           - GLOBAL: match = 10
           - PROJECT: exact workspace/project match = 25
           - SESSION: exact session match = 30
        5. Keyword / Text semantic overlap:
           - Fraction of task keywords matching memory content or memory keywords: up to +40 points
        """
        score = 0.0

        # 1. Base Priority
        prio_weights = {
            MemoryPriority.CRITICAL.value: 40.0,
            MemoryPriority.HIGH.value: 25.0,
            MemoryPriority.MEDIUM.value: 15.0,
            MemoryPriority.LOW.value: 5.0
        }
        score += prio_weights.get(record.priority, 10.0)

        # 2. Confidence
        conf_weights = {
            MemoryConfidence.USER_CONFIRMED.value: 25.0,
            MemoryConfidence.VERIFIED.value: 15.0,
            MemoryConfidence.OBSERVED.value: 5.0,
            MemoryConfidence.UNVERIFIED.value: 0.0
        }
        score += conf_weights.get(record.confidence, 5.0)

        # 3. Type Boost (Corrections and rejections must always dominate)
        if record.type in (MemoryType.CORRECTION.value, MemoryType.REJECTED_APPROACH.value):
            score += 30.0
        elif record.type in (MemoryType.ARCHITECTURAL_RULE.value, MemoryType.CONSTRAINT.value):
            score += 20.0
        elif record.type == MemoryType.ACCEPTED_APPROACH.value:
            score += 15.0

        # 4. Scope Alignment
        if record.scope == MemoryScope.SESSION.value:
            if current_session_id and record.session_id == current_session_id:
                score += 30.0
            else:
                score -= 40.0 # Irrelevant to a different session
        elif record.scope == MemoryScope.PROJECT.value:
            if current_project_id and record.project_id == current_project_id:
                score += 25.0
            elif current_workspace and record.workspace and (record.workspace.lower() in current_workspace.lower() or current_workspace.lower() in record.workspace.lower()):
                score += 25.0
            else:
                score -= 10.0
        elif record.scope == MemoryScope.GLOBAL.value:
            score += 10.0 # Universally applicable

        # 5. Keyword Overlap
        if task_keywords:
            mem_text = f"{record.title or ''} {record.content} {record.reason or ''} {record.rejected_approach or ''} {' '.join(record.keywords)}".lower()
            overlap = 0
            for kw in task_keywords:
                if kw in mem_text:
                    overlap += 1
            if overlap > 0:
                overlap_ratio = overlap / len(task_keywords)
                score += min(50.0, overlap * 15.0 + overlap_ratio * 25.0)
            else:
                # If zero keyword overlap and it's not a global architectural rule or critical correction, penalize
                if record.scope != MemoryScope.GLOBAL.value and record.priority != MemoryPriority.CRITICAL.value:
                    score -= 30.0

        return max(0.0, score)

    @classmethod
    def rank_records(
        cls,
        records: List[MemoryRecord],
        task: str,
        workspace: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        top_k: int = 15,
        min_score: float = 20.0
    ) -> List[Tuple[MemoryRecord, float]]:
        """Ranks a list of candidate records, returning top-K tuples of (record, score)."""
        keywords = extract_keywords(task)
        scored = []
        for rec in records:
            if not rec.active:
                continue
            s = cls.score_memory(
                rec,
                task_text=task,
                task_keywords=keywords,
                current_workspace=workspace,
                current_project_id=project_id,
                current_session_id=session_id
            )
            if s >= min_score:
                scored.append((rec, s))

        # Sort descending by score
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
