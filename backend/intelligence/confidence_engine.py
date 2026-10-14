"""
Agy Studio v2.6 — Confidence Engine
Implements evidence-based confidence hierarchy:
USER_CONFIRMED > VERIFIED > SUPPORTED > OBSERVED > HYPOTHESIS.
"""

from enum import Enum
from typing import Dict, Any, Optional

class ConfidenceLevel(str, Enum):
    HYPOTHESIS = "HYPOTHESIS"
    OBSERVED = "OBSERVED"
    SUPPORTED = "SUPPORTED"
    VERIFIED = "VERIFIED"
    USER_CONFIRMED = "USER_CONFIRMED"

CONFIDENCE_ORDER = {
    ConfidenceLevel.HYPOTHESIS.value: 1,
    ConfidenceLevel.OBSERVED.value: 2,
    ConfidenceLevel.SUPPORTED.value: 3,
    ConfidenceLevel.VERIFIED.value: 4,
    ConfidenceLevel.USER_CONFIRMED.value: 5,
}

class ConfidenceEngine:
    """Manages confidence calculations, evidence checks, and level transitions."""

    @staticmethod
    def get_rank(level: str) -> int:
        return CONFIDENCE_ORDER.get(str(level).upper(), 1)

    @staticmethod
    def is_greater_or_equal(level_a: str, level_b: str) -> bool:
        return ConfidenceEngine.get_rank(level_a) >= ConfidenceEngine.get_rank(level_b)

    @staticmethod
    def promote_with_evidence(
        current_level: str,
        evidence_type: str,
        success: bool,
        is_user_confirmed: bool = False
    ) -> str:
        if is_user_confirmed:
            return ConfidenceLevel.USER_CONFIRMED.value

        current_rank = ConfidenceEngine.get_rank(current_level)

        if not success:
            # Demote on failure
            if current_rank > 1:
                ranks = {v: k for k, v in CONFIDENCE_ORDER.items()}
                return ranks.get(current_rank - 1, ConfidenceLevel.HYPOTHESIS.value)
            return ConfidenceLevel.HYPOTHESIS.value

        # Success path
        if evidence_type in ["TEST_PASS", "ARTIFACT_HASH_VERIFIED", "RUNTIME_PROBE_SUCCESS", "HWND_VERIFIED"]:
            return ConfidenceLevel.VERIFIED.value
        elif evidence_type in ["EXIT_CODE_ZERO", "OUTPUT_PARSED"]:
            if current_rank < 3:
                return ConfidenceLevel.SUPPORTED.value
            return current_level
        elif evidence_type in ["OBSERVED_RUN"]:
            if current_rank < 2:
                return ConfidenceLevel.OBSERVED.value
            return current_level

        return current_level

    @staticmethod
    def demote_on_conflict(current_level: str, reason: str = "") -> str:
        # A contradiction or conflict pulls confidence down
        current_rank = ConfidenceEngine.get_rank(current_level)
        if current_rank >= 4:
            return ConfidenceLevel.SUPPORTED.value
        return ConfidenceLevel.HYPOTHESIS.value
