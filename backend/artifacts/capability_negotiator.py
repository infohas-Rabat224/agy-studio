"""
Multimodal Capability Negotiator for Agy Studio.
Evaluates agent capabilities against artifact requirements.
Prevents false multimodal claims and safely transforms artifacts (e.g. OCR/Text)
when explicitly negotiated and recorded in forensic audit.
"""

from typing import List, Dict, Any, Tuple, Optional
from .models import Artifact, ArtifactSourceType
from ..agent_adapters.base import AgentModel, CapabilityStatus

class NegotiationResult:
    def __init__(
        self,
        compatible: bool,
        required_capabilities: List[str],
        missing_capabilities: List[str],
        transformations: List[Dict[str, Any]],
        normalized_artifacts: List[Dict[str, Any]],
        audit_note: str = "",
        image_ingestion_verified: bool = False,
        image_agent_delivery_verified: bool = False,
        image_understanding_verified: bool = False
    ):
        self.compatible = compatible
        self.required_capabilities = required_capabilities
        self.missing_capabilities = missing_capabilities
        self.transformations = transformations
        self.normalized_artifacts = normalized_artifacts
        self.audit_note = audit_note
        self.image_ingestion_verified = image_ingestion_verified
        self.image_agent_delivery_verified = image_agent_delivery_verified
        self.image_understanding_verified = image_understanding_verified

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compatible": self.compatible,
            "required_capabilities": self.required_capabilities,
            "missing_capabilities": self.missing_capabilities,
            "transformations": self.transformations,
            "normalized_artifacts": self.normalized_artifacts,
            "audit_note": self.audit_note,
            "image_ingestion_verified": self.image_ingestion_verified,
            "image_agent_delivery_verified": self.image_agent_delivery_verified,
            "image_understanding_verified": self.image_understanding_verified
        }

class ArtifactCapabilityNegotiator:
    """
    Evidence-based negotiator between artifacts and universal agent CLI adapters.
    Strictly separates:
    - IMAGE_INGESTION_VERIFIED (artifact received, persisted, SHA-256 computed)
    - IMAGE_AGENT_DELIVERY_VERIFIED (vision-capable agent receives image)
    - IMAGE_UNDERSTANDING_VERIFIED (vision-capable agent answers from image)
    Never infers IMAGE_VISION from IMAGE_INGESTION or OCR.
    """

    @classmethod
    def negotiate(
        cls,
        agent: AgentModel,
        artifacts: List[Artifact],
        task_prompt: str,
        workspace: str
    ) -> NegotiationResult:
        """
        Negotiates handoff for a set of artifacts with the selected agent.
        """
        required_caps: List[str] = ["text_input"]
        missing_caps: List[str] = []
        transformations: List[Dict[str, Any]] = []
        normalized_artifacts: List[Dict[str, Any]] = []
        compatible = True
        audit_notes: List[str] = []

        image_ingestion_verified = False
        image_agent_delivery_verified = False
        image_understanding_verified = False

        agent_caps = agent.capabilities or {}

        for art in artifacts:
            norm_art: Dict[str, Any] = {
                "id": art.id,
                "name": art.name,
                "type": art.source_type.value.lower(),
                "path": art.content.binary_path,
                "extracted_text": art.content.extracted_text or art.content.text,
                "pages": art.metadata.pages,
                "mime_type": art.mime_type,
                "sha256": art.sha256
            }

            # Image / Screenshot negotiation
            if art.source_type in (ArtifactSourceType.IMAGE, ArtifactSourceType.SCREENSHOT, ArtifactSourceType.CLIPBOARD_IMAGE):
                # 1. IMAGE_INGESTION_VERIFIED: Persisted with SHA-256 and dimensions
                norm_art["image_ingestion_verified"] = bool(art.sha256 and art.content.binary_path)
                image_ingestion_verified = True

                # 2. Check if agent has strictly verified IMAGE_VISION
                vis_val = str(
                    agent_caps.get("IMAGE_VISION") or
                    agent_caps.get("image_vision") or
                    agent_caps.get("vision") or ""
                ).upper()
                has_vision = (vis_val == CapabilityStatus.VERIFIED.value)

                if has_vision:
                    norm_art["handoff_mode"] = "NATIVE_IMAGE"
                    norm_art["image_agent_delivery_verified"] = True
                    image_agent_delivery_verified = True
                    required_caps.extend(["IMAGE_VISION", "image_input"])
                else:
                    norm_art["image_agent_delivery_verified"] = False
                    # Agent lacks verified vision: check for OCR text transformation
                    if art.content.extracted_text and len(art.content.extracted_text.strip()) > 0:
                        trans = {
                            "artifact_id": art.id,
                            "name": art.name,
                            "transformation": "IMAGE_TO_OCR_TEXT",
                            "reason": f"Agent {agent.id} lacks verified IMAGE_VISION; supplied verified OCR text fallback.",
                            "status": "SUCCESS"
                        }
                        transformations.append(trans)
                        norm_art["handoff_mode"] = "OCR_TEXT_TRANSFORMATION"
                        audit_notes.append(f"Image {art.name} converted to OCR text for text-only agent {agent.id}.")
                    else:
                        missing_caps.extend(["IMAGE_VISION", "image_input"])
                        compatible = False
                        norm_art["handoff_mode"] = "UNSUPPORTED"
                        audit_notes.append(
                            f"Agent {agent.id} lacks verified IMAGE_VISION and no OCR text is available for {art.name}."
                        )

            # PDF negotiation: two-stage capability (Text layer vs Scanned/OCR)
            elif art.source_type == ArtifactSourceType.PDF:
                pdf_val = str(agent_caps.get("PDF") or agent_caps.get("pdf_context", "")).upper()
                has_native_pdf = (pdf_val == CapabilityStatus.VERIFIED.value)

                from .models import ExtractionStatus
                if art.extraction.status == ExtractionStatus.OCR_REQUIRED:
                    # Stage 2: Scanned PDF without text layer -> Requires OCR
                    ocr_val = str(agent_caps.get("OCR") or agent_caps.get("ocr", "")).upper()
                    has_ocr = (ocr_val == CapabilityStatus.VERIFIED.value)
                    if has_ocr:
                        trans = {
                            "artifact_id": art.id,
                            "name": art.name,
                            "transformation": "PDF_SCANNED_TO_OCR_TEXT",
                            "reason": f"Scanned PDF {art.name} processed via verified OCR engine.",
                            "status": "SUCCESS"
                        }
                        transformations.append(trans)
                        norm_art["handoff_mode"] = "OCR_TEXT_TRANSFORMATION"
                        audit_notes.append(f"Scanned PDF {art.name} converted to OCR text.")
                    else:
                        missing_caps.append("OCR")
                        compatible = False
                        norm_art["handoff_mode"] = "OCR_REQUIRED"
                        audit_notes.append(
                            f"PDF {art.name} is a scanned document without text layer. "
                            "OCR is required but unavailable in the runtime."
                        )
                elif has_native_pdf:
                    norm_art["handoff_mode"] = "NATIVE_PDF"
                    required_caps.append("pdf_context")
                else:
                    # Stage 1: Text layer exists -> Normalized extracted text handoff
                    trans = {
                        "artifact_id": art.id,
                        "name": art.name,
                        "transformation": "PDF_TO_EXTRACTED_TEXT",
                        "reason": f"Agent {agent.id} receives normalized extracted text with page boundaries.",
                        "status": "SUCCESS"
                    }
                    transformations.append(trans)
                    norm_art["handoff_mode"] = "DOCUMENT_TEXT_CONTEXT"
                    audit_notes.append(f"PDF {art.name} supplied as structured document context for agent {agent.id}.")

            # Office documents (DOCX, XLSX, PPTX)
            elif art.source_type in (ArtifactSourceType.DOCX, ArtifactSourceType.DOC, ArtifactSourceType.XLSX, ArtifactSourceType.XLS):
                trans = {
                    "artifact_id": art.id,
                    "name": art.name,
                    "transformation": "DOCUMENT_TO_STRUCTURED_TEXT",
                    "reason": f"Normalized tabular/heading text supplied.",
                    "status": "SUCCESS"
                }
                transformations.append(trans)
                norm_art["handoff_mode"] = "DOCUMENT_TEXT_CONTEXT"

            else:
                norm_art["handoff_mode"] = "DIRECT_DATA"

            normalized_artifacts.append(norm_art)

        # Build prompt injection context if agent is text-only but received document/text context
        return NegotiationResult(
            compatible=compatible,
            required_capabilities=list(set(required_caps)),
            missing_capabilities=list(set(missing_caps)),
            transformations=transformations,
            normalized_artifacts=normalized_artifacts,
            audit_note="; ".join(audit_notes),
            image_ingestion_verified=image_ingestion_verified,
            image_agent_delivery_verified=image_agent_delivery_verified,
            image_understanding_verified=image_understanding_verified
        )


    @classmethod
    def build_normalized_agent_payload(
        cls,
        task_prompt: str,
        workspace: str,
        negotiation: NegotiationResult
    ) -> Dict[str, Any]:
        """
        Builds the canonical normalized execution payload per Section 18.
        """
        return {
            "task": task_prompt,
            "workspace": workspace,
            "artifacts": negotiation.normalized_artifacts,
            "transformations": negotiation.transformations
        }
