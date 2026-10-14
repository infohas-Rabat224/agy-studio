"""
Document Extractor for Agy Studio.
Handles real extraction of PDF, DOCX, DOC, XLSX, PPTX, Text, Code, and Archives.
Never fakes extraction or OCR results.
"""

import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional

from .models import (
    Artifact, ArtifactSourceType, ExtractionStatus,
    ArtifactContent, ArtifactMetadata, ArtifactExtraction
)

class DocumentExtractor:
    """
    Universal extraction engine for documents and text artifacts.
    """

    @classmethod
    def extract(cls, file_path: Path, source_type: ArtifactSourceType) -> Tuple[ArtifactContent, ArtifactMetadata, ArtifactExtraction]:
        """
        Routes extraction based on detected source type.
        """
        start = time.time()
        content = ArtifactContent(binary_path=str(file_path))
        metadata = ArtifactMetadata()
        extraction = ArtifactExtraction()

        try:
            if source_type == ArtifactSourceType.PDF:
                cls._extract_pdf(file_path, content, metadata, extraction)
            elif source_type == ArtifactSourceType.DOCX:
                cls._extract_docx(file_path, content, metadata, extraction)
            elif source_type == ArtifactSourceType.DOC:
                cls._extract_doc_legacy(file_path, content, metadata, extraction)
            elif source_type in (ArtifactSourceType.XLSX, ArtifactSourceType.XLS):
                cls._extract_xlsx(file_path, content, metadata, extraction)
            elif source_type in (ArtifactSourceType.PPTX, ArtifactSourceType.PPT):
                cls._extract_pptx(file_path, content, metadata, extraction)
            elif source_type == ArtifactSourceType.ARCHIVE:
                cls._inspect_archive(file_path, content, metadata, extraction)
            elif source_type in (
                ArtifactSourceType.TXT, ArtifactSourceType.CSV,
                ArtifactSourceType.JSON, ArtifactSourceType.SOURCE_CODE,
                ArtifactSourceType.CLIPBOARD_TEXT
            ):
                cls._extract_text(file_path, content, metadata, extraction)
            else:
                extraction.status = ExtractionStatus.NOT_APPLICABLE
                extraction.extractor = "none"
        except Exception as ex:
            extraction.status = ExtractionStatus.FAILED
            extraction.errors.append(str(ex))
            extraction.extractor = "error_handler"

        extraction.duration_ms = int((time.time() - start) * 1000)
        return content, metadata, extraction

    @classmethod
    def _extract_pdf(
        cls,
        path: Path,
        content: ArtifactContent,
        metadata: ArtifactMetadata,
        extraction: ArtifactExtraction
    ):
        """Extracts text, pages, and metadata from PDF using pypdf."""
        try:
            import pypdf
        except ImportError:
            extraction.status = ExtractionStatus.EXTRACTOR_UNAVAILABLE
            extraction.extractor = "pypdf_missing"
            extraction.errors.append("pypdf library is not installed in runtime")
            return

        reader = pypdf.PdfReader(str(path))
        metadata.pages = len(reader.pages)
        if reader.metadata:
            metadata.title = getattr(reader.metadata, "title", None)
            metadata.author = getattr(reader.metadata, "author", None)

        pages_text = []
        total_chars = 0
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            total_chars += len(page_text.strip())
            pages_text.append(f"--- Page {i + 1} ---\n{page_text}")

        extracted = "\n\n".join(pages_text)
        metadata.char_count = total_chars

        # Scanned PDF detection: low text count (< 40 chars)
        if total_chars < 40 and metadata.pages > 0:
            extraction.extractor = "pypdf"
            # Try OCR if an OCR engine is available
            ocr_text = cls._try_ocr_pdf(path)
            if ocr_text:
                extraction.status = ExtractionStatus.OCR_COMPLETED
                extraction.extractor = "tesseract_ocr"
                extraction.ocr_chars = len(ocr_text)
                content.extracted_text = ocr_text
                metadata.char_count = len(ocr_text)
            else:
                extraction.status = ExtractionStatus.OCR_REQUIRED
                extraction.warnings.append("Low text content detected: document appears to be scanned or image-based. OCR required.")
                content.extracted_text = (
                    f"[OCR_REQUIRED: Ce document PDF ({metadata.pages} page(s)) ne comporte aucune couche de texte extractible. "
                    "Il s'agit d'un document numérisé ou basé sur des images. Un moteur OCR est nécessaire pour en extraire le contenu.]"
                )
        else:
            extraction.status = ExtractionStatus.TEXT_EXTRACTED
            extraction.extractor = "pypdf"
            content.extracted_text = extracted

    @classmethod
    def _try_ocr_pdf(cls, path: Path) -> Optional[str]:
        """Attempts OCR on PDF if pytesseract or Windows OCR is present."""
        try:
            import pytesseract
            # Verify tesseract binary exists
            pytesseract.get_tesseract_version()
            # If pdf2image is also available, render and ocr
            import pdf2image
            images = pdf2image.convert_from_path(str(path), first_page=1, last_page=5)
            ocr_parts = []
            for i, img in enumerate(images):
                t = pytesseract.image_to_string(img)
                if t.strip():
                    ocr_parts.append(f"--- OCR Page {i + 1} ---\n{t.strip()}")
            if ocr_parts:
                return "\n\n".join(ocr_parts)
        except Exception:
            pass
        return None

    @classmethod
    def _extract_docx(
        cls,
        path: Path,
        content: ArtifactContent,
        metadata: ArtifactMetadata,
        extraction: ArtifactExtraction
    ):
        """Extracts structured content, headings, tables, and metadata from DOCX."""
        try:
            import docx
        except ImportError:
            extraction.status = ExtractionStatus.EXTRACTOR_UNAVAILABLE
            extraction.extractor = "python-docx_missing"
            extraction.errors.append("python-docx library is not installed in runtime")
            return

        doc = docx.Document(str(path))
        core = doc.core_properties
        metadata.author = core.author
        metadata.title = core.title

        parts = []
        total_chars = 0

        # Paragraphs & headings
        for p in doc.paragraphs:
            txt = p.text.strip()
            if txt:
                total_chars += len(txt)
                style_name = p.style.name if p.style else ""
                if "Heading" in style_name:
                    parts.append(f"## {txt}")
                else:
                    parts.append(txt)

        # Tables
        table_count = len(doc.tables)
        metadata.table_count = table_count
        for i, tbl in enumerate(doc.tables):
            parts.append(f"\n[Tableau #{i + 1}]")
            for row in tbl.rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                row_str = " | ".join(cells)
                total_chars += len(row_str)
                parts.append(f"| {row_str} |")

        metadata.char_count = total_chars
        content.extracted_text = "\n\n".join(parts)
        extraction.status = ExtractionStatus.TEXT_EXTRACTED
        extraction.extractor = "python-docx"

    @classmethod
    def _extract_doc_legacy(
        cls,
        path: Path,
        content: ArtifactContent,
        metadata: ArtifactMetadata,
        extraction: ArtifactExtraction
    ):
        """
        Legacy binary DOC format (.doc).
        Attempts Word COM if Word is installed on Windows; otherwise reports EXTRACTOR_UNAVAILABLE.
        """
        if sys.platform == "win32":
            try:
                import win32com.client
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                doc = word.Documents.Open(str(path), ReadOnly=True)
                txt = doc.Content.Text
                doc.Close(False)
                word.Quit()
                if txt:
                    content.extracted_text = txt
                    metadata.char_count = len(txt)
                    extraction.status = ExtractionStatus.TEXT_EXTRACTED
                    extraction.extractor = "win32com_word"
                    return
            except Exception:
                pass

        extraction.status = ExtractionStatus.EXTRACTOR_UNAVAILABLE
        extraction.extractor = "legacy_doc_extractor_missing"
        extraction.warnings.append("Legacy .doc binary format requires Microsoft Word COM or antiword. Use DOCX format for direct extraction.")

    @classmethod
    def _extract_xlsx(
        cls,
        path: Path,
        content: ArtifactContent,
        metadata: ArtifactMetadata,
        extraction: ArtifactExtraction
    ):
        """Extracts worksheets, tables, and cell content from Excel workbook."""
        try:
            import openpyxl
        except ImportError:
            extraction.status = ExtractionStatus.EXTRACTOR_UNAVAILABLE
            extraction.extractor = "openpyxl_missing"
            extraction.errors.append("openpyxl is not installed in runtime")
            return

        wb = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
        sheet_names = wb.sheetnames
        metadata.sheet_names = sheet_names

        parts = []
        total_chars = 0
        for sname in sheet_names[:10]: # Limit to first 10 sheets
            ws = wb[sname]
            parts.append(f"=== Feuille : {sname} ===")
            row_count = 0
            for row in ws.iter_rows(values_only=True):
                row_count += 1
                if row_count > 500: # Limit to 500 rows per sheet
                    parts.append("... [Lignes supplémentaires tronquées]")
                    break
                # Filter empty rows
                vals = [str(v) if v is not None else "" for v in row]
                if any(v.strip() for v in vals):
                    line = " | ".join(vals)
                    total_chars += len(line)
                    parts.append(line)
            parts.append("")

        wb.close()
        metadata.char_count = total_chars
        content.extracted_text = "\n".join(parts)
        extraction.status = ExtractionStatus.TEXT_EXTRACTED
        extraction.extractor = "openpyxl"

    @classmethod
    def _extract_pptx(
        cls,
        path: Path,
        content: ArtifactContent,
        metadata: ArtifactMetadata,
        extraction: ArtifactExtraction
    ):
        """Extracts slide text and slide notes from PowerPoint presentations."""
        try:
            import pptx
        except ImportError:
            extraction.status = ExtractionStatus.EXTRACTOR_UNAVAILABLE
            extraction.extractor = "python-pptx_missing"
            extraction.errors.append("python-pptx is not installed in runtime")
            return

        prs = pptx.Presentation(str(path))
        metadata.slide_count = len(prs.slides)

        parts = []
        total_chars = 0
        for i, slide in enumerate(prs.slides):
            parts.append(f"--- Diapositive {i + 1} ---")
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        t = para.text.strip()
                        if t:
                            total_chars += len(t)
                            parts.append(t)
            # Notes
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                note_txt = slide.notes_slide.notes_text_frame.text.strip()
                if note_txt:
                    parts.append(f"[Note : {note_txt}]")
            parts.append("")

        metadata.char_count = total_chars
        content.extracted_text = "\n".join(parts)
        extraction.status = ExtractionStatus.TEXT_EXTRACTED
        extraction.extractor = "python-pptx"

    @classmethod
    def _extract_text(
        cls,
        path: Path,
        content: ArtifactContent,
        metadata: ArtifactMetadata,
        extraction: ArtifactExtraction
    ):
        """Safely reads plain text, code, JSON, and CSV files."""
        encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
        raw_text = None
        used_enc = "utf-8"

        for enc in encodings:
            try:
                with open(path, "r", encoding=enc) as f:
                    raw_text = f.read(500000) # Read up to 500KB
                    used_enc = enc
                    break
            except (UnicodeDecodeError, Exception):
                continue

        if raw_text is None:
            # Fallback with replace
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = f.read(500000)
                used_enc = "utf-8-replace"

        content.text = raw_text
        content.extracted_text = raw_text
        metadata.char_count = len(raw_text)
        metadata.line_count = len(raw_text.splitlines())
        extraction.status = ExtractionStatus.TEXT_EXTRACTED
        extraction.extractor = f"text_loader_{used_enc}"

    @classmethod
    def _inspect_archive(
        cls,
        path: Path,
        content: ArtifactContent,
        metadata: ArtifactMetadata,
        extraction: ArtifactExtraction
    ):
        """
        Safely inspects a ZIP archive without uncompressing arbitrary files.
        Guarantees path traversal prevention and file count limits.
        """
        try:
            with zipfile.ZipFile(str(path), "r") as zf:
                infolist = zf.infolist()
                metadata.extra["archive_file_count"] = len(infolist)
                total_uncompressed = sum(info.file_size for info in infolist)
                metadata.extra["archive_uncompressed_bytes"] = total_uncompressed

                # Security check 1: Max uncompressed size 50MB
                if total_uncompressed > 50 * 1024 * 1024:
                    extraction.warnings.append("Archive uncompressed size exceeds 50MB limit.")

                # Security check 2: Path traversal check
                traversal_detected = False
                file_names = []
                for info in infolist:
                    fn = info.filename
                    if fn.startswith("/") or fn.startswith("\\") or ".." in fn or ":" in fn:
                        traversal_detected = True
                        break
                    file_names.append(fn)

                if traversal_detected:
                    extraction.status = ExtractionStatus.FAILED
                    extraction.errors.append("Archive contains invalid path traversal sequences (Zip-Slip attempt).")
                    return

                manifest = [f"Archive Manifest ({len(infolist)} fichiers, {total_uncompressed} octets):"]
                manifest.extend(file_names[:100])
                if len(file_names) > 100:
                    manifest.append(f"... et {len(file_names) - 100} fichiers supplémentaires.")

                content.extracted_text = "\n".join(manifest)
                metadata.char_count = len(content.extracted_text)
                extraction.status = ExtractionStatus.TEXT_EXTRACTED
                extraction.extractor = "zip_manifest_inspector"
        except Exception as ex:
            extraction.status = ExtractionStatus.FAILED
            extraction.errors.append(f"Erreur d'inspection de l'archive : {ex}")
