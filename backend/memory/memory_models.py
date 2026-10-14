"""
Agy Studio — Persistent Learning Memory System: Models & Schemas
Defines memory scopes, types, confidence levels, priority tiers, and data transfer models.
"""

import time
import uuid
import secrets
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class MemoryScope(str, Enum):
    GLOBAL = "GLOBAL"
    PROJECT = "PROJECT"
    SESSION = "SESSION"

class MemoryType(str, Enum):
    CORRECTION = "CORRECTION"
    DECISION = "DECISION"
    CONSTRAINT = "CONSTRAINT"
    PREFERENCE = "PREFERENCE"
    LESSON = "LESSON"
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"
    REJECTED_APPROACH = "REJECTED_APPROACH"
    ACCEPTED_APPROACH = "ACCEPTED_APPROACH"
    BUG = "BUG"
    WORKAROUND = "WORKAROUND"
    TODO = "TODO"
    REQUIREMENT = "REQUIREMENT"
    ARCHITECTURAL_RULE = "ARCHITECTURAL_RULE"

class MemoryConfidence(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    OBSERVED = "OBSERVED"
    VERIFIED = "VERIFIED"
    USER_CONFIRMED = "USER_CONFIRMED"

class MemoryPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class MemoryRecord:
    def __init__(
        self,
        memory_id: Optional[str] = None,
        scope: str = MemoryScope.PROJECT.value,
        type: str = MemoryType.LESSON.value,
        content: str = "",
        title: Optional[str] = None,
        reason: Optional[str] = None,
        source: str = "USER",
        confidence: str = MemoryConfidence.OBSERVED.value,
        priority: str = MemoryPriority.MEDIUM.value,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workspace: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        evidence_refs: Optional[List[str]] = None,
        rejected_approach: Optional[str] = None,
        accepted_alternative: Optional[str] = None,
        active: bool = True,
        superseded_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.memory_id = memory_id or self.generate_id()
        self.scope = scope
        self.type = type
        self.content = content.strip()
        self.title = title or (content[:60] + "..." if len(content) > 60 else content)
        self.reason = reason
        self.source = source
        self.confidence = confidence
        self.priority = priority
        self.created_at = created_at or now_iso
        self.updated_at = updated_at or now_iso
        self.session_id = session_id
        self.project_id = project_id
        self.workspace = workspace
        self.keywords = keywords or []
        self.evidence_refs = evidence_refs or []
        self.rejected_approach = rejected_approach
        self.accepted_alternative = accepted_alternative
        self.active = active
        self.superseded_by = superseded_by
        self.metadata = metadata or {}

    @staticmethod
    def generate_id() -> str:
        date_str = time.strftime("%Y%m%d", time.gmtime())
        token = secrets.token_hex(4).upper()
        return f"MEM-{date_str}-{token}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "scope": self.scope,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "reason": self.reason,
            "source": self.source,
            "confidence": self.confidence,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "session_id": self.session_id,
            "project_id": self.project_id,
            "workspace": self.workspace,
            "keywords": self.keywords,
            "evidence_refs": self.evidence_refs,
            "rejected_approach": self.rejected_approach,
            "accepted_alternative": self.accepted_alternative,
            "active": self.active,
            "superseded_by": self.superseded_by,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryRecord":
        return cls(
            memory_id=data.get("memory_id"),
            scope=data.get("scope", MemoryScope.PROJECT.value),
            type=data.get("type", MemoryType.LESSON.value),
            content=data.get("content", ""),
            title=data.get("title"),
            reason=data.get("reason"),
            source=data.get("source", "USER"),
            confidence=data.get("confidence", MemoryConfidence.OBSERVED.value),
            priority=data.get("priority", MemoryPriority.MEDIUM.value),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            session_id=data.get("session_id"),
            project_id=data.get("project_id"),
            workspace=data.get("workspace"),
            keywords=data.get("keywords", []),
            evidence_refs=data.get("evidence_refs", []),
            rejected_approach=data.get("rejected_approach"),
            accepted_alternative=data.get("accepted_alternative"),
            active=data.get("active", True),
            superseded_by=data.get("superseded_by"),
            metadata=data.get("metadata", {})
        )

# Pydantic Schemas for FastAPI
class MemoryCreateRequest(BaseModel):
    scope: str = "PROJECT" # GLOBAL, PROJECT, SESSION
    type: str = "LESSON" # CORRECTION, REJECTED_APPROACH, ACCEPTED_APPROACH, CONSTRAINT, etc.
    content: str
    title: Optional[str] = None
    reason: Optional[str] = None
    source: str = "USER"
    confidence: str = "USER_CONFIRMED"
    priority: str = "HIGH"
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    workspace: Optional[str] = None
    keywords: Optional[List[str]] = None
    evidence_refs: Optional[List[str]] = None
    rejected_approach: Optional[str] = None
    accepted_alternative: Optional[str] = None

class MemoryConfirmRequest(BaseModel):
    scope: Optional[str] = None
    priority: Optional[str] = None

class MemorySupersedeRequest(BaseModel):
    new_memory_id: str
    reason: Optional[str] = None

class PreflightRequest(BaseModel):
    task: str
    workspace: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    agent_id: Optional[str] = None

class GuardCheckRequest(BaseModel):
    proposal: str
    workspace: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None

class PreflightResult(BaseModel):
    task: str
    has_critical_corrections: bool
    has_rejected_approaches: bool
    corrections: List[Dict[str, Any]]
    rejected_approaches: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    accepted_approaches: List[Dict[str, Any]]
    lessons: List[Dict[str, Any]]
    potential_risks: List[str]
    context_injection_markdown: str
    formatted_prompt_block: Optional[str] = None

class GuardResult(BaseModel):
    allowed: bool
    violation: bool
    warning: Optional[str] = None
    rejected_pattern: Optional[str] = None
    reason: Optional[str] = None
    accepted_alternative: Optional[str] = None
    evidence_session_id: Optional[str] = None
