"""
Universal Artifact Model for Agy Studio.
Provides normalized schema for all multimodal inputs (images, screenshots, PDFs,
Office docs, source code, text, archives).
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ArtifactSourceType(str, Enum):
    IMAGE = "IMAGE"
    SCREENSHOT = "SCREENSHOT"
    CLIPBOARD_IMAGE = "CLIPBOARD_IMAGE"
    CLIPBOARD_TEXT = "CLIPBOARD_TEXT"
    PDF = "PDF"
    DOC = "DOC"
    DOCX = "DOCX"
    XLS = "XLS"
    XLSX = "XLSX"
    PPT = "PPT"
    PPTX = "PPTX"
    CSV = "CSV"
    TXT = "TXT"
    SOURCE_CODE = "SOURCE_CODE"
    JSON = "JSON"
    ARCHIVE = "ARCHIVE"
    BINARY = "BINARY"
    UNKNOWN = "UNKNOWN"

class ArtifactAcquisition(str, Enum):
    WORKSPACE = "workspace"
    FILE_PICKER = "file_picker"
    CLIPBOARD = "clipboard"
    DRAG_DROP = "drag_drop"
    PASTE = "paste"
    GENERATED = "generated"

class ExtractionStatus(str, Enum):
    PENDING = "PENDING"
    TEXT_EXTRACTED = "TEXT_EXTRACTED"
    OCR_REQUIRED = "OCR_REQUIRED"
    OCR_COMPLETED = "OCR_COMPLETED"
    OCR_FAILED = "OCR_FAILED"
    EXTRACTOR_UNAVAILABLE = "EXTRACTOR_UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    FAILED = "FAILED"

class ArtifactContent(BaseModel):
    text: Optional[str] = None
    binary_path: str = ""
    image_path: Optional[str] = None
    extracted_text: Optional[str] = None

class ArtifactMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    pages: Optional[int] = None
    author: Optional[str] = None
    title: Optional[str] = None
    language: Optional[str] = None
    sheet_names: List[str] = Field(default_factory=list)
    slide_count: Optional[int] = None
    char_count: Optional[int] = None
    line_count: Optional[int] = None
    table_count: Optional[int] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

class ArtifactExtraction(BaseModel):
    status: ExtractionStatus = ExtractionStatus.PENDING
    extractor: Optional[str] = None
    duration_ms: int = 0
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    ocr_chars: int = 0

class ArtifactSecurity(BaseModel):
    allowed: bool = True
    quarantined: bool = False
    reason: Optional[str] = None

class Artifact(BaseModel):
    id: str
    session_id: str
    name: str
    source_type: ArtifactSourceType = ArtifactSourceType.UNKNOWN
    source_path: Optional[str] = None
    mime_type: str = "application/octet-stream"
    extension: str = ""
    size_bytes: int = 0
    sha256: str = ""
    created_at: str = ""
    modified_at: str = ""
    acquisition: ArtifactAcquisition = ArtifactAcquisition.WORKSPACE

    content: ArtifactContent = Field(default_factory=ArtifactContent)
    metadata: ArtifactMetadata = Field(default_factory=ArtifactMetadata)
    extraction: ArtifactExtraction = Field(default_factory=ArtifactExtraction)
    security: ArtifactSecurity = Field(default_factory=ArtifactSecurity)

    def to_summary_dict(self) -> Dict[str, Any]:
        """Provides concise representation for UI and agent context."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "name": self.name,
            "source_type": self.source_type.value,
            "mime_type": self.mime_type,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "acquisition": self.acquisition.value,
            "extraction_status": self.extraction.status.value,
            "extractor": self.extraction.extractor,
            "pages": self.metadata.pages,
            "dimensions": f"{self.metadata.width}x{self.metadata.height}" if self.metadata.width and self.metadata.height else None,
            "char_count": self.metadata.char_count,
            "created_at": self.created_at,
            "has_extracted_text": bool(self.content.extracted_text or self.content.text),
            "preview_available": bool(self.content.image_path or self.content.extracted_text or self.content.text)
        }

    def to_prompt_context(self, max_chars: int = 4000) -> str:
        """Normalized representation of the artifact for agent prompt injection."""
        header = f"[ARTEFACT: {self.name} | MIME: {self.mime_type} | Taille: {self.size_bytes} octets | SHA256: {self.sha256[:12]}...]"
        if self.content.extracted_text:
            text = self.content.extracted_text.strip()
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n... [Contenu tronqué à {max_chars} caractères / Total: {len(self.content.extracted_text)}]"
            return f"{header}\nContenu extrait ({self.extraction.extractor}) :\n{text}\n"
        elif self.content.text:
            text = self.content.text.strip()
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n... [Contenu tronqué à {max_chars} caractères / Total: {len(self.content.text)}]"
            return f"{header}\nContenu textuel :\n{text}\n"
        elif self.metadata.width and self.metadata.height:
            return f"{header}\nImage ({self.metadata.width}x{self.metadata.height} px). Fichier : {self.content.binary_path}\n"
        else:
            return f"{header}\nFichier binaire. Fichier : {self.content.binary_path}\n"

