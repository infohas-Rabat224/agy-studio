"""
Centralized Backend Preview Service for Agy Studio.
Orchestrates:
1. Artifact resolution from ArtifactManager store
2. File existence and size limit validation
3. MIME spoofing and security policy validation
4. Renderer dispatch based on PREVIEW_SUPPORT_MATRIX
5. Formatted preview response generation for frontend Real Preview panel
"""

import os
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .preview_config import (
    REAL_PREVIEW_ENABLED,
    PREVIEW_MAX_SIZE,
    PreviewMode,
    PreviewSecurityPolicy,
    PREVIEW_SUPPORT_MATRIX,
    detect_mime_spoofing
)
from .preview_renderer import PreviewRenderer

class PreviewService:
    """Authoritative preview service for all workspace files and multimodal artifacts."""

    def __init__(self, data_dir: Optional[Path] = None, artifacts_manager: Any = None):
        self.data_dir = data_dir or (Path(__file__).resolve().parent.parent.parent / "data")
        self._artifacts_manager = artifacts_manager

    @property
    def artifact_manager(self):
        if self._artifacts_manager is None:
            from ..artifacts.artifact_manager import ArtifactManager
            self._artifacts_manager = ArtifactManager(self.data_dir)
        return self._artifacts_manager

    def resolve_artifact_preview(self, artifact_id: str) -> Dict[str, Any]:
        """
        Resolves an artifact by ID from the artifact store and generates
        a safe, verified preview representation.
        """
        if not REAL_PREVIEW_ENABLED:
            return {
                "preview_enabled": False,
                "status": "DISABLED",
                "message": "Real Preview is disabled in application configuration."
            }

        art = self.artifact_manager.get_artifact(artifact_id)
        if not art:
            return {
                "preview_enabled": True,
                "status": "NOT_FOUND",
                "error": f"Artifact {artifact_id} introuvable."
            }

        bin_path = Path(art.content.binary_path)
        if not bin_path.exists():
            return {
                "preview_enabled": True,
                "status": "FILE_MISSING",
                "error": f"Fichier binaire manquant sur le disque : {art.content.binary_path}"
            }

        return self._resolve_path_preview(
            file_path=bin_path,
            artifact_id=art.id,
            display_name=art.name,
            declared_mime=art.mime_type
        )

    def resolve_file_preview(self, file_path: Path) -> Dict[str, Any]:
        """
        Resolves an arbitrary workspace file and generates a safe preview representation.
        """
        if not REAL_PREVIEW_ENABLED:
            return {
                "preview_enabled": False,
                "status": "DISABLED",
                "message": "Real Preview is disabled in application configuration."
            }

        if not file_path.exists():
            return {
                "preview_enabled": True,
                "status": "NOT_FOUND",
                "error": f"Fichier introuvable : {file_path}"
            }

        return self._resolve_path_preview(
            file_path=file_path,
            artifact_id=None,
            display_name=file_path.name
        )

    def _resolve_path_preview(
        self,
        file_path: Path,
        artifact_id: Optional[str] = None,
        display_name: Optional[str] = None,
        declared_mime: Optional[str] = None
    ) -> Dict[str, Any]:
        """Internal deterministic preview resolution and security enforcement."""
        if not file_path.exists():
            return {
                "preview_enabled": True,
                "status": "NOT_FOUND",
                "artifact_id": artifact_id,
                "name": display_name or file_path.name,
                "error": f"Fichier introuvable sur le disque : {file_path}"
            }

        ext = file_path.suffix.lower()
        stat = file_path.stat()
        file_size = stat.st_size
        name = display_name or file_path.name

        # URL for downloading raw binary
        if artifact_id:
            raw_url = f"/api/artifacts/{artifact_id}/content"
            preview_raw_url = f"/api/artifacts/{artifact_id}/preview/raw"
        else:
            safe_enc = urllib.parse.quote(str(file_path))
            raw_url = f"/api/file/raw?path={safe_enc}"
            preview_raw_url = f"/api/file/raw?path={safe_enc}"

        # 1. Size Limit Check
        if file_size > PREVIEW_MAX_SIZE:
            return {
                "preview_enabled": True,
                "status": "OVERSIZED",
                "artifact_id": artifact_id,
                "name": name,
                "size_bytes": file_size,
                "extension": ext,
                "preview_mode": PreviewMode.UNSUPPORTED.value,
                "preview_type": "oversized",
                "error": f"Fichier trop volumineux ({file_size / (1024*1024):.1f} MB > {PREVIEW_MAX_SIZE / (1024*1024):.0f} MB). Téléchargement disponible.",
                "raw_url": raw_url
            }

        # 2. MIME Spoofing Check (Section 7A.12)
        spoof_err = detect_mime_spoofing(file_path, ext)
        if spoof_err:
            return {
                "preview_enabled": True,
                "status": "SECURITY_BLOCKED",
                "artifact_id": artifact_id,
                "name": name,
                "size_bytes": file_size,
                "extension": ext,
                "preview_mode": PreviewMode.UNSUPPORTED.value,
                "preview_type": "blocked",
                "error": f"Aperçu bloqué pour raison de sécurité : {spoof_err}",
                "raw_url": raw_url,
                "security": {"allowed": False, "quarantined": True, "reason": spoof_err}
            }

        # 3. Support Matrix Lookup
        matrix_entry = PREVIEW_SUPPORT_MATRIX.get(ext)
        if not matrix_entry or not matrix_entry.get("enabled", False):
            mode = matrix_entry.get("mode", PreviewMode.UNSUPPORTED.value) if matrix_entry else PreviewMode.UNSUPPORTED.value
            return {
                "preview_enabled": True,
                "status": "UNSUPPORTED",
                "artifact_id": artifact_id,
                "name": name,
                "size_bytes": file_size,
                "extension": ext,
                "preview_mode": mode,
                "preview_type": "unsupported",
                "message": f"Aperçu non pris en charge pour ce type de fichier ({ext}). Le fichier reste disponible au téléchargement.",
                "raw_url": raw_url,
                "security": {"allowed": True, "quarantined": False}
            }

        # 4. Dispatch Renderer by Extension/Category
        mode = matrix_entry["mode"]
        renderer = matrix_entry["renderer"]
        mime = matrix_entry["mime"]

        res: Dict[str, Any] = {
            "preview_enabled": True,
            "status": "READY",
            "artifact_id": artifact_id,
            "name": name,
            "path": str(file_path),
            "size_bytes": file_size,
            "extension": ext,
            "mime_type": mime,
            "preview_mode": mode,
            "preview_type": renderer,
            "raw_url": raw_url,
            "preview_raw_url": preview_raw_url,
            "security": {"allowed": True, "quarantined": False}
        }

        # Native PDF
        if renderer == "pdf":
            res["preview_type"] = "pdf"
            res["content_url"] = preview_raw_url

        # Native Image
        elif renderer == "image":
            res["preview_type"] = "image"
            res["content_url"] = preview_raw_url

        # DOCX Converted
        elif renderer == "docx":
            res["preview_type"] = "docx"
            render_res = PreviewRenderer.render_docx(file_path)
            res["content"] = render_res.get("html", "")
            res["metadata"] = render_res
            # Check for candidate PDF companion
            cand_pdf = file_path.with_suffix(".pdf")
            if cand_pdf.exists():
                safe_cand = urllib.parse.quote(str(cand_pdf))
                res["has_pdf_companion"] = True
                res["pdf_companion_url"] = f"/api/file/raw?path={safe_cand}"
            else:
                res["has_pdf_companion"] = False

        # XLSX Converted
        elif renderer == "xlsx":
            res["preview_type"] = "xlsx"
            render_res = PreviewRenderer.render_xlsx(file_path)
            res["content"] = render_res.get("html", "")
            res["sheets"] = render_res.get("sheets", [])
            res["sheet_names"] = render_res.get("sheet_names", [])

        # PPTX Converted
        elif renderer == "pptx":
            res["preview_type"] = "pptx"
            render_res = PreviewRenderer.render_pptx(file_path)
            res["content"] = render_res.get("html", "")
            res["slides"] = render_res.get("slides", [])
            res["slide_count"] = render_res.get("slide_count", 0)

        # CSV Table
        elif renderer == "table":
            res["preview_type"] = "table"
            render_res = PreviewRenderer.render_csv(file_path)
            res["content"] = render_res.get("html", "")
            res["row_count"] = render_res.get("row_count", 0)

        # SVG Sanitized
        elif renderer == "svg":
            res["preview_type"] = "svg"
            render_res = PreviewRenderer.render_svg(file_path)
            res["content"] = render_res.get("html", "")

        # HTML Sandboxed
        elif renderer == "html":
            res["preview_type"] = "html"
            res["content_url"] = preview_raw_url

        # Markdown Sanitized
        elif renderer == "markdown":
            res["preview_type"] = "markdown"
            text_res = PreviewRenderer.render_text_or_code(file_path)
            res["content"] = text_res.get("content", "")

        # Text & Source Code
        elif renderer in ("text", "code"):
            res["preview_type"] = "code" if renderer == "code" else "text"
            text_res = PreviewRenderer.render_text_or_code(file_path)
            res["content"] = text_res.get("content", "")
            res["line_count"] = text_res.get("line_count", 0)
            res["char_count"] = text_res.get("char_count", 0)

        return res

# Global Singleton Service
preview_service = PreviewService()
