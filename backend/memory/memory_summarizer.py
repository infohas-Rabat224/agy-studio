"""
Agy Studio — Memory Summarizer & Context Builder
Formats structured pre-flight briefs, warnings, and prompt injection markdown.
"""

from typing import List, Dict, Any
from .memory_models import MemoryRecord, MemoryType

class MemorySummarizer:
    @staticmethod
    def format_preflight_context(
        task: str,
        corrections: List[MemoryRecord],
        rejected: List[MemoryRecord],
        constraints: List[MemoryRecord],
        accepted: List[MemoryRecord],
        lessons: List[MemoryRecord]
    ) -> str:
        """Constructs a clean, high-priority context block to inject into the agent prompt."""
        sections = []

        if corrections:
            lines = ["🚨 EXPLICIT USER CORRECTIONS & CRITICAL RULES:"]
            for i, c in enumerate(corrections, 1):
                prio_badge = f"[{c.priority}]" if c.priority else ""
                lines.append(f"  {i}. {prio_badge} {c.content}")
                if c.reason:
                    lines.append(f"     Reason: {c.reason}")
            sections.append("\n".join(lines))

        if rejected:
            lines = ["🚫 PREVIOUSLY REJECTED APPROACHES (DO NOT PROPOSE OR REINTRODUCE):"]
            for i, r in enumerate(rejected, 1):
                appr = r.rejected_approach or r.content
                lines.append(f"  {i}. REJECTED: {appr}")
                if r.reason:
                    lines.append(f"     WHY REJECTED: {r.reason}")
                if r.accepted_alternative:
                    lines.append(f"     ACCEPTED ALTERNATIVE TO USE INSTEAD: {r.accepted_alternative}")
            sections.append("\n".join(lines))

        if constraints:
            lines = ["📐 ARCHITECTURAL CONSTRAINTS & REQUIREMENTS:"]
            for i, k in enumerate(constraints, 1):
                lines.append(f"  {i}. {k.content}")
            sections.append("\n".join(lines))

        if accepted:
            lines = ["✅ PREVIOUSLY ACCEPTED & VERIFIED IMPLEMENTATIONS:"]
            for i, a in enumerate(accepted, 1):
                lines.append(f"  {i}. {a.accepted_alternative or a.content}")
            sections.append("\n".join(lines))

        if lessons:
            lines = ["💡 LESSONS LEARNED & KNOWN WORKAROUNDS:"]
            for i, l in enumerate(lessons, 1):
                lines.append(f"  {i}. {l.content}")
            sections.append("\n".join(lines))

        if not sections:
            return ""

        header = "=== AGY STUDIO PRE-FLIGHT LEARNING MEMORY CONTEXT ==="
        footer = "====================================================="
        body = "\n\n".join(sections)
        return f"{header}\n{body}\n{footer}\n"

    @staticmethod
    def identify_potential_risks(task: str, rejected: List[MemoryRecord], constraints: List[MemoryRecord]) -> List[str]:
        """Infers regression risks from task text against rejected items and constraints."""
        risks = []
        t_lower = task.lower()
        for r in rejected:
            r_text = (r.rejected_approach or r.content).lower()
            # If task mentions similar domain
            if any(term in t_lower for term in r_text.split() if len(term) > 3):
                risks.append(f"Risk of regressing into rejected approach: '{r.rejected_approach or r.content}' (Reason: {r.reason or 'User rejected'})")

        for c in constraints:
            if "mock" in c.content.lower() and ("mock" in t_lower or "test" in t_lower):
                risks.append("Constraint violation risk: System forbids mocks without real runtime verification.")
            if "provider-agnostic" in c.content.lower() and any(p in t_lower for p in ["claude", "qwen", "cline", "adapter"]):
                risks.append("Constraint violation risk: Universal Agent Runtime must remain provider-agnostic.")
        return risks
