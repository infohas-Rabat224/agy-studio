"""
Artifact Manager for Agy Studio.
Orchestrates artifact acquisition, storage isolation, SHA-256 calculation,
extraction routing, preview generation, and correlation with SessionManager.
"""

import os
import re
import time
import json
import shutil
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from .models import (
    Artifact, ArtifactSourceType, ArtifactAcquisition,
    ExtractionStatus, ArtifactContent, ArtifactMetadata,
    ArtifactExtraction, ArtifactSecurity
)
from .document_extractor import DocumentExtractor
from .image_processor import ImageProcessor, SUPPORTED_IMAGE_EXTENSIONS
from .clipboard_manager import ClipboardManager

MIME_TYPE_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".json": "application/json",
    ".csv": "text/csv",
    ".xml": "application/xml",
    ".yaml": "application/x-yaml",
    ".yml": "application/x-yaml",
    ".py": "text/x-python",
    ".js": "text/javascript",
    ".ts": "text/typescript",
    ".jsx": "text/javascript",
    ".tsx": "text/typescript",
    ".html": "text/html",
    ".css": "text/css",
    ".sql": "text/x-sql",
    ".ps1": "text/x-powershell",
    ".bat": "text/x-bat",
    ".cmd": "text/x-bat",
    ".c": "text/x-c",
    ".cpp": "text/x-c++",
    ".java": "text/x-java",
    ".php": "text/x-php",
    ".sh": "text/x-sh",
    ".zip": "application/zip",
}

SOURCE_CODE_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
    ".c", ".cpp", ".h", ".hpp", ".java", ".php", ".sql",
    ".ps1", ".bat", ".cmd", ".sh", ".rs", ".go"
}

def sanitize_filename(filename: str) -> str:
    """Sanitizes filename against path traversal and dangerous characters."""
    norm = filename.replace("\\", "/").rstrip("/")
    base = os.path.basename(norm)
    while ".." in base:
        base = base.replace("..", "")
    base = base.replace("/", "").replace("\\", "").strip()
    name, ext = os.path.splitext(base)
    safe_name = re.sub(r"[^\w\s\.\-]", "_", name).strip()
    if not safe_name:
        safe_name = "unnamed_artifact"
    return f"{safe_name}{ext}"

def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

class ArtifactManager:
    """
    Central hub for universal artifact storage and metadata management.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (Path(__file__).resolve().parent.parent.parent / "data")
        self.artifacts_root = self.data_dir / "artifacts"
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.sessions_dir = self.data_dir / "sessions"

    def _get_target_dir(self, session_id: Optional[str]) -> Path:
        """Determines storage location: session-specific or global."""
        if session_id:
            td = self.sessions_dir / session_id / "artifacts"
        else:
            td = self.artifacts_root
        td.mkdir(parents=True, exist_ok=True)
        return td

    def detect_source_type(self, ext: str, acquisition: ArtifactAcquisition) -> ArtifactSourceType:
        """Determines ArtifactSourceType based on extension and acquisition."""
        ext = ext.lower()
        if acquisition in (ArtifactAcquisition.CLIPBOARD, ArtifactAcquisition.PASTE) and ext in SUPPORTED_IMAGE_EXTENSIONS:
            return ArtifactSourceType.SCREENSHOT
        if ext in SUPPORTED_IMAGE_EXTENSIONS:
            return ArtifactSourceType.IMAGE
        if ext == ".pdf":
            return ArtifactSourceType.PDF
        if ext == ".docx":
            return ArtifactSourceType.DOCX
        if ext == ".doc":
            return ArtifactSourceType.DOC
        if ext in (".xlsx", ".xls"):
            return ArtifactSourceType.XLSX if ext == ".xlsx" else ArtifactSourceType.XLS
        if ext in (".pptx", ".ppt"):
            return ArtifactSourceType.PPTX if ext == ".pptx" else ArtifactSourceType.PPT
        if ext == ".csv":
            return ArtifactSourceType.CSV
        if ext == ".json":
            return ArtifactSourceType.JSON
        if ext in SOURCE_CODE_EXTS:
            return ArtifactSourceType.SOURCE_CODE
        if ext in (".txt", ".md", ".log"):
            return ArtifactSourceType.TXT
        if ext == ".zip":
            return ArtifactSourceType.ARCHIVE
        return ArtifactSourceType.UNKNOWN

    def ingest_file(
        self,
        source: Union[Path, str, bytes],
        filename: str,
        acquisition: ArtifactAcquisition = ArtifactAcquisition.WORKSPACE,
        session_id: Optional[str] = None,
        source_path: Optional[str] = None
    ) -> Artifact:
        """
        Ingests a real file or bytes into the artifact store.
        Calculates SHA-256, validates security, and extracts metadata.
        """
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        art_id = f"art_{int(time.time()*1000)}_{os.urandom(3).hex()}"
        safe_name = sanitize_filename(filename)
        ext = os.path.splitext(safe_name)[1].lower()
        mime = MIME_TYPE_MAP.get(ext, "application/octet-stream")

        target_dir = self._get_target_dir(session_id)
        stored_path = target_dir / f"{art_id}_{safe_name}"

        # Write or copy file
        if isinstance(source, bytes):
            with open(stored_path, "wb") as f:
                f.write(source)
        elif isinstance(source, (Path, str)):
            src_p = Path(source)
            if not src_p.exists():
                raise FileNotFoundError(f"Source file not found: {source}")
            shutil.copy2(str(src_p), str(stored_path))

        stat = stored_path.stat()
        sha256 = compute_sha256(stored_path)
        source_type = self.detect_source_type(ext, acquisition)

        artifact = Artifact(
            id=art_id,
            session_id=session_id or "default",
            name=safe_name,
            source_type=source_type,
            source_path=source_path or (str(source) if isinstance(source, (Path, str)) else None),
            mime_type=mime,
            extension=ext,
            size_bytes=stat.st_size,
            sha256=sha256,
            created_at=now_iso,
            modified_at=now_iso,
            acquisition=acquisition,
            content=ArtifactContent(binary_path=str(stored_path)),
            security=ArtifactSecurity(allowed=True, quarantined=False)
        )

        # Security check on executable uploads
        if ext in (".exe", ".dll", ".so", ".dylib"):
            artifact.security.quarantined = True
            artifact.security.allowed = False
            artifact.security.reason = "Executable binaries are quarantined and blocked from execution."
            artifact.extraction.status = ExtractionStatus.FAILED
            artifact.extraction.errors.append(artifact.security.reason)
            self._save_metadata(artifact)
            return artifact

        # Route extraction
        if source_type in (ArtifactSourceType.IMAGE, ArtifactSourceType.SCREENSHOT, ArtifactSourceType.CLIPBOARD_IMAGE):
            meta, ext_info, prev_path = ImageProcessor.process_image(stored_path)
            artifact.metadata = meta
            artifact.extraction = ext_info
            artifact.content.image_path = prev_path
        else:
            content, meta, ext_info = DocumentExtractor.extract(stored_path, source_type)
            artifact.content = content
            artifact.metadata = meta
            artifact.extraction = ext_info

        self._save_metadata(artifact)

        # Correlate with SessionManager if session_id provided
        try:
            from ..session.session_manager import SessionManager
            sm = SessionManager.get_instance(self.data_dir)
            if sm.get_current_session() and sm.get_current_session().session_id == (session_id or "default"):
                sm.attach_artifact(
                    artifact_id=artifact.id,
                    name=artifact.name,
                    artifact_type=artifact.source_type.value,
                    source=artifact.acquisition.value,
                    path=str(stored_path),
                    sha256=artifact.sha256,
                    size_bytes=artifact.size_bytes
                )
        except Exception:
            pass

        return artifact

    def ingest_clipboard(self, session_id: Optional[str] = None) -> Tuple[Optional[Artifact], str]:
        """
        Reads native Windows desktop clipboard and creates an artifact.
        Returns (artifact, status_message).
        """
        clip_type, data, err_msg = ClipboardManager.read_native_clipboard()
        if clip_type == "none" or data is None:
            return None, err_msg or "Presse-papiers vide ou non pris en charge."

        if clip_type == "image":
            # Data is PIL Image
            import io
            buf = io.BytesIO()
            data.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            filename = f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"
            art = self.ingest_file(
                source=img_bytes,
                filename=filename,
                acquisition=ArtifactAcquisition.CLIPBOARD,
                session_id=session_id
            )
            dim_str = f"{art.metadata.width}×{art.metadata.height}" if art.metadata.width else ""
            mb_str = f"{art.size_bytes / (1024*1024):.1f} MB" if art.size_bytes >= 1024*1024 else f"{art.size_bytes / 1024:.0f} KB"
            msg = f"✓ Capture d'écran enregistrée ({dim_str} • {mb_str})"
            return art, msg

        elif clip_type == "files":
            # Data is List[str]
            first_art = None
            ingested_count = 0
            for fp in data:
                if os.path.exists(fp):
                    art = self.ingest_file(
                        source=Path(fp),
                        filename=os.path.basename(fp),
                        acquisition=ArtifactAcquisition.CLIPBOARD,
                        session_id=session_id,
                        source_path=fp
                    )
                    if not first_art:
                        first_art = art
                    ingested_count += 1
            msg = f"✓ {ingested_count} fichier(s) du presse-papiers ingéré(s)"
            return first_art, msg

        elif clip_type == "text":
            # Data is str
            txt_bytes = data.encode("utf-8")
            filename = f"clipboard_text_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            art = self.ingest_file(
                source=txt_bytes,
                filename=filename,
                acquisition=ArtifactAcquisition.CLIPBOARD,
                session_id=session_id
            )
            msg = f"✓ Texte du presse-papiers ingéré ({len(data)} caractères)"
            return art, msg

        return None, "Format de presse-papiers non pris en charge."

    def _save_metadata(self, artifact: Artifact):
        """Saves artifact metadata JSON alongside binary."""
        meta_path = Path(artifact.content.binary_path).with_suffix(".meta.json")
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(artifact.model_dump(), f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Loads artifact by ID across all session and global artifact folders."""
        # Check global artifacts
        for m_file in self.artifacts_root.glob(f"{artifact_id}_*.meta.json"):
            try:
                with open(m_file, "r", encoding="utf-8") as f:
                    return Artifact(**json.load(f))
            except Exception:
                pass

        # Check sessions
        if self.sessions_dir.exists():
            for m_file in self.sessions_dir.glob(f"*/artifacts/{artifact_id}_*.meta.json"):
                try:
                    with open(m_file, "r", encoding="utf-8") as f:
                        return Artifact(**json.load(f))
                except Exception:
                    pass
        return None

    def list_artifacts(self, session_id: Optional[str] = None) -> List[Artifact]:
        """Lists artifacts for a given session or globally."""
        results = []
        target_dir = self._get_target_dir(session_id)
        for m_file in target_dir.glob("*.meta.json"):
            try:
                with open(m_file, "r", encoding="utf-8") as f:
                    results.append(Artifact(**json.load(f)))
            except Exception:
                pass
        results.sort(key=lambda a: a.created_at, reverse=True)
        return results

    def delete_artifact(self, artifact_id: str) -> bool:
        """Deletes artifact binary and metadata files."""
        art = self.get_artifact(artifact_id)
        if not art:
            return False
        try:
            bin_p = Path(art.content.binary_path)
            meta_p = bin_p.with_suffix(".meta.json")
            if bin_p.exists():
                bin_p.unlink()
            if meta_p.exists():
                meta_p.unlink()
            return True
        except Exception:
            return False
