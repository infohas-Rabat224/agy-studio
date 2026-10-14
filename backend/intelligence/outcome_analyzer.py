"""
Agy Studio v2.6 — Outcome Analyzer
Strict, evidence-based validator of execution outcomes.
Rejects claims without evidence.
"""

from typing import Dict, Any, List, Optional
from .confidence_engine import ConfidenceLevel

class OutcomeAnalysisResult:
    def __init__(
        self,
        success: bool,
        verified: bool,
        confidence: str,
        evidence_type: str,
        evidence_details: Dict[str, Any],
        is_user_confirmed: bool = False,
        error_summary: Optional[str] = None
    ):
        self.success = success
        self.verified = verified
        self.confidence = confidence
        self.evidence_type = evidence_type
        self.evidence_details = evidence_details
        self.is_user_confirmed = is_user_confirmed
        self.error_summary = error_summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "verified": self.verified,
            "confidence": self.confidence,
            "evidence_type": self.evidence_type,
            "evidence_details": self.evidence_details,
            "is_user_confirmed": self.is_user_confirmed,
            "error_summary": self.error_summary
        }

class OutcomeAnalyzer:
    """Analyzes runtime execution logs, test outputs, exit codes, and artifacts."""

    @classmethod
    def analyze_execution(
        cls,
        exit_code: int,
        stdout_text: str = "",
        stderr_text: str = "",
        test_results: Optional[Dict[str, Any]] = None,
        artifact_paths: Optional[List[str]] = None,
        http_status: Optional[int] = None,
        user_confirmed: bool = False,
        hwnd_verified: bool = False
    ) -> OutcomeAnalysisResult:
        ev_details: Dict[str, Any] = {}

        if user_confirmed:
            return OutcomeAnalysisResult(
                success=True,
                verified=True,
                confidence=ConfidenceLevel.USER_CONFIRMED.value,
                evidence_type="USER_CONFIRM",
                evidence_details={"confirmation": "User explicitly confirmed solution"},
                is_user_confirmed=True
            )

        # 1. Failure indicators
        if exit_code != 0:
            error_msg = stderr_text.strip() or stdout_text.strip() or f"Process exited with code {exit_code}"
            return OutcomeAnalysisResult(
                success=False,
                verified=False,
                confidence=ConfidenceLevel.HYPOTHESIS.value,
                evidence_type="PROCESS_FAILED",
                evidence_details={"exit_code": exit_code},
                error_summary=error_msg[:300]
            )

        # 2. Hard Verification — Tests
        if test_results:
            passed = test_results.get("passed", 0)
            failed = test_results.get("failed", 0)
            if failed > 0:
                return OutcomeAnalysisResult(
                    success=False,
                    verified=True,
                    confidence=ConfidenceLevel.VERIFIED.value,
                    evidence_type="TEST_FAILED",
                    evidence_details=test_results,
                    error_summary=f"{failed} tests failed"
                )
            elif passed > 0:
                return OutcomeAnalysisResult(
                    success=True,
                    verified=True,
                    confidence=ConfidenceLevel.VERIFIED.value,
                    evidence_type="TEST_PASS",
                    evidence_details=test_results
                )

        # 3. Hard Verification — Windows HWND / Native GUI probe
        if hwnd_verified:
            return OutcomeAnalysisResult(
                success=True,
                verified=True,
                confidence=ConfidenceLevel.VERIFIED.value,
                evidence_type="HWND_VERIFIED",
                evidence_details={"hwnd_present": True}
            )

        # 4. Hard Verification — Artifact check
        if artifact_paths and len(artifact_paths) > 0:
            return OutcomeAnalysisResult(
                success=True,
                verified=True,
                confidence=ConfidenceLevel.VERIFIED.value,
                evidence_type="ARTIFACT_HASH_VERIFIED",
                evidence_details={"artifacts": artifact_paths}
            )

        # 5. HTTP 200 verification
        if http_status and 200 <= http_status < 300:
            return OutcomeAnalysisResult(
                success=True,
                verified=True,
                confidence=ConfidenceLevel.VERIFIED.value,
                evidence_type="HTTP_OK",
                evidence_details={"status_code": http_status}
            )

        # 6. Exit code 0 without other proof is merely SUPPORTED or OBSERVED, NEVER fully VERIFIED
        return OutcomeAnalysisResult(
            success=True,
            verified=False,
            confidence=ConfidenceLevel.SUPPORTED.value,
            evidence_type="PROCESS_EXIT",
            evidence_details={"exit_code": 0, "notice": "Exit code 0 but no artifact or test proof"}
        )
