"""
Centralized Configuration & Safe Preview Support Matrix for Agy Studio.
Enforces Section 5 and Section 7A requirements:
- Authoritative REAL_PREVIEW_ENABLED flag
- Machine-readable PREVIEW_SUPPORT_MATRIX
- MIME spoofing detection and execution prevention invariants
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional

# Section 1 & Section 5: Authoritative Preview Enablement
REAL_PREVIEW_ENABLED: bool = True

# Section 25: Large file protection threshold (50 MB default)
PREVIEW_MAX_SIZE: int = 50 * 1024 * 1024

class PreviewMode(str, Enum):
    NATIVE = "NATIVE"
    SANITIZED = "SANITIZED"
    SANDBOXED = "SANDBOXED"
    CONVERTED = "CONVERTED"
    TEXT_ONLY = "TEXT_ONLY"
    TABLE = "TABLE"
    UNSUPPORTED = "UNSUPPORTED"

class PreviewSecurityPolicy(str, Enum):
    SAFE_TEXT = "SAFE_TEXT"
    NEVER_EXECUTE = "NEVER_EXECUTE"
    PARSED_DATA = "PARSED_DATA"
    SANITIZED_HTML = "SANITIZED_HTML"
    SANDBOXED_VIEWER = "SANDBOXED_VIEWER"
    IMAGE_ONLY = "IMAGE_ONLY"
    STRIP_ACTIVE_CONTENT = "STRIP_ACTIVE_CONTENT"
    SANDBOXED_IFRAME = "SANDBOXED_IFRAME"
    SANITIZED_CONVERSION = "SANITIZED_CONVERSION"
    DATA_ONLY_RENDERING = "DATA_ONLY_RENDERING"
    SOURCE_DISPLAY_ONLY = "SOURCE_DISPLAY_ONLY"
    BLOCKED_BINARY = "BLOCKED_BINARY"
    DOWNLOAD_ONLY = "DOWNLOAD_ONLY"

# Section 7A.1 & 7A.15: Machine-Readable Safe Preview Support Matrix
PREVIEW_SUPPORT_MATRIX: Dict[str, Dict[str, Any]] = {
    # Plain text & Logs
    ".txt": {
        "mime": "text/plain",
        "category": "Plain text",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "text",
        "enabled": True,
        "security": PreviewSecurityPolicy.SAFE_TEXT.value,
        "description": "Safe text rendering"
    },
    ".log": {
        "mime": "text/plain",
        "category": "Logs",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "text",
        "enabled": True,
        "security": PreviewSecurityPolicy.SAFE_TEXT.value,
        "description": "Safe text rendering"
    },
    ".json": {
        "mime": "application/json",
        "category": "JSON",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "text",
        "enabled": True,
        "security": PreviewSecurityPolicy.NEVER_EXECUTE.value,
        "description": "Never execute, formatted JSON view"
    },
    ".xml": {
        "mime": "application/xml",
        "category": "XML",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "text",
        "enabled": True,
        "security": PreviewSecurityPolicy.NEVER_EXECUTE.value,
        "description": "Never execute, formatted XML view"
    },
    ".yaml": {
        "mime": "text/yaml",
        "category": "YAML",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "text",
        "enabled": True,
        "security": PreviewSecurityPolicy.NEVER_EXECUTE.value,
        "description": "Never execute, formatted YAML view"
    },
    ".yml": {
        "mime": "text/yaml",
        "category": "YAML",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "text",
        "enabled": True,
        "security": PreviewSecurityPolicy.NEVER_EXECUTE.value,
        "description": "Never execute, formatted YAML view"
    },
    # Tabular Data
    ".csv": {
        "mime": "text/csv",
        "category": "CSV",
        "mode": PreviewMode.TABLE.value,
        "renderer": "table",
        "enabled": True,
        "security": PreviewSecurityPolicy.PARSED_DATA.value,
        "description": "Parsed and rendered as structured data table"
    },
    # Markdown
    ".md": {
        "mime": "text/markdown",
        "category": "Markdown",
        "mode": PreviewMode.SANITIZED.value,
        "renderer": "markdown",
        "enabled": True,
        "security": PreviewSecurityPolicy.SANITIZED_HTML.value,
        "description": "HTML output sanitized, scripts stripped"
    },
    ".markdown": {
        "mime": "text/markdown",
        "category": "Markdown",
        "mode": PreviewMode.SANITIZED.value,
        "renderer": "markdown",
        "enabled": True,
        "security": PreviewSecurityPolicy.SANITIZED_HTML.value,
        "description": "HTML output sanitized, scripts stripped"
    },
    # PDF
    ".pdf": {
        "mime": "application/pdf",
        "category": "PDF",
        "mode": PreviewMode.NATIVE.value,
        "renderer": "pdf",
        "enabled": True,
        "security": PreviewSecurityPolicy.SANDBOXED_VIEWER.value,
        "description": "Sandboxed PDF viewer"
    },
    # Raster Images
    ".png": {
        "mime": "image/png",
        "category": "Image",
        "mode": PreviewMode.NATIVE.value,
        "renderer": "image",
        "enabled": True,
        "security": PreviewSecurityPolicy.IMAGE_ONLY.value,
        "description": "Verified image only"
    },
    ".jpg": {
        "mime": "image/jpeg",
        "category": "Image",
        "mode": PreviewMode.NATIVE.value,
        "renderer": "image",
        "enabled": True,
        "security": PreviewSecurityPolicy.IMAGE_ONLY.value,
        "description": "Verified image only"
    },
    ".jpeg": {
        "mime": "image/jpeg",
        "category": "Image",
        "mode": PreviewMode.NATIVE.value,
        "renderer": "image",
        "enabled": True,
        "security": PreviewSecurityPolicy.IMAGE_ONLY.value,
        "description": "Verified image only"
    },
    ".webp": {
        "mime": "image/webp",
        "category": "Image",
        "mode": PreviewMode.NATIVE.value,
        "renderer": "image",
        "enabled": True,
        "security": PreviewSecurityPolicy.IMAGE_ONLY.value,
        "description": "Verified image only"
    },
    ".gif": {
        "mime": "image/gif",
        "category": "Image",
        "mode": PreviewMode.NATIVE.value,
        "renderer": "image",
        "enabled": True,
        "security": PreviewSecurityPolicy.IMAGE_ONLY.value,
        "description": "Verified image only"
    },
    ".bmp": {
        "mime": "image/bmp",
        "category": "Image",
        "mode": PreviewMode.NATIVE.value,
        "renderer": "image",
        "enabled": True,
        "security": PreviewSecurityPolicy.IMAGE_ONLY.value,
        "description": "Verified image only"
    },
    # Vector Images / SVG
    ".svg": {
        "mime": "image/svg+xml",
        "category": "SVG",
        "mode": PreviewMode.SANITIZED.value,
        "renderer": "svg",
        "enabled": True,
        "security": PreviewSecurityPolicy.STRIP_ACTIVE_CONTENT.value,
        "description": "Strip active script tags, event handlers, and javascript: links"
    },
    # HTML
    ".html": {
        "mime": "text/html",
        "category": "HTML",
        "mode": PreviewMode.SANDBOXED.value,
        "renderer": "html",
        "enabled": True,
        "security": PreviewSecurityPolicy.SANDBOXED_IFRAME.value,
        "description": "Sandboxed iframe, no parent access, isolated origin"
    },
    ".htm": {
        "mime": "text/html",
        "category": "HTML",
        "mode": PreviewMode.SANDBOXED.value,
        "renderer": "html",
        "enabled": True,
        "security": PreviewSecurityPolicy.SANDBOXED_IFRAME.value,
        "description": "Sandboxed iframe, no parent access, isolated origin"
    },
    # Office Documents
    ".docx": {
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "category": "DOCX",
        "mode": PreviewMode.CONVERTED.value,
        "renderer": "docx",
        "enabled": True,
        "security": PreviewSecurityPolicy.SANITIZED_CONVERSION.value,
        "description": "Sanitized document conversion without macro execution"
    },
    ".xlsx": {
        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "category": "XLSX",
        "mode": PreviewMode.CONVERTED.value,
        "renderer": "xlsx",
        "enabled": True,
        "security": PreviewSecurityPolicy.DATA_ONLY_RENDERING.value,
        "description": "Data-only tabular rendering, formulas never executed"
    },
    ".pptx": {
        "mime": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "category": "PPTX",
        "mode": PreviewMode.CONVERTED.value,
        "renderer": "pptx",
        "enabled": True,
        "security": PreviewSecurityPolicy.SANITIZED_CONVERSION.value,
        "description": "Sanitized slide deck rendering without active content"
    },
    ".rtf": {
        "mime": "application/rtf",
        "category": "RTF",
        "mode": PreviewMode.CONVERTED.value,
        "renderer": "text",
        "enabled": True,
        "security": PreviewSecurityPolicy.SAFE_TEXT.value,
        "description": "Sanitized plain text extraction"
    },
    # Source Code (Section 7A.2: NEVER EXECUTE, DISPLAY SOURCE ONLY)
    ".js": {
        "mime": "text/javascript",
        "category": "JavaScript",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "code",
        "enabled": True,
        "security": PreviewSecurityPolicy.SOURCE_DISPLAY_ONLY.value,
        "description": "Display source code only. Never execute."
    },
    ".ts": {
        "mime": "text/typescript",
        "category": "TypeScript",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "code",
        "enabled": True,
        "security": PreviewSecurityPolicy.SOURCE_DISPLAY_ONLY.value,
        "description": "Display source code only. Never execute."
    },
    ".py": {
        "mime": "text/x-python",
        "category": "Python",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "code",
        "enabled": True,
        "security": PreviewSecurityPolicy.SOURCE_DISPLAY_ONLY.value,
        "description": "Display source code only. Never execute."
    },
    ".sh": {
        "mime": "text/x-sh",
        "category": "Shell script",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "code",
        "enabled": True,
        "security": PreviewSecurityPolicy.SOURCE_DISPLAY_ONLY.value,
        "description": "Display source code only. Never execute."
    },
    ".sql": {
        "mime": "text/x-sql",
        "category": "SQL",
        "mode": PreviewMode.TEXT_ONLY.value,
        "renderer": "code",
        "enabled": True,
        "security": PreviewSecurityPolicy.SOURCE_DISPLAY_ONLY.value,
        "description": "Display source code only. Never execute."
    },
    # Unsupported Binaries / Archives (Never preview, download only)
    ".zip": {
        "mime": "application/zip",
        "category": "Archive",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.DOWNLOAD_ONLY.value,
        "description": "Archive decompression prohibited during preview. Download only."
    },
    ".7z": {
        "mime": "application/x-7z-compressed",
        "category": "Archive",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.DOWNLOAD_ONLY.value,
        "description": "Download only."
    },
    ".rar": {
        "mime": "application/vnd.rar",
        "category": "Archive",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.DOWNLOAD_ONLY.value,
        "description": "Download only."
    },
    ".tar": {
        "mime": "application/x-tar",
        "category": "Archive",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.DOWNLOAD_ONLY.value,
        "description": "Download only."
    },
    ".gz": {
        "mime": "application/gzip",
        "category": "Archive",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.DOWNLOAD_ONLY.value,
        "description": "Download only."
    },
    # Executables & Scripts (Never preview, never execute)
    ".exe": {
        "mime": "application/vnd.microsoft.portable-executable",
        "category": "Executable",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.BLOCKED_BINARY.value,
        "description": "Executable binary preview prohibited. Never execute."
    },
    ".dll": {
        "mime": "application/octet-stream",
        "category": "PE Binary",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.BLOCKED_BINARY.value,
        "description": "PE binary preview prohibited."
    },
    ".msi": {
        "mime": "application/x-msi",
        "category": "Installer",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.BLOCKED_BINARY.value,
        "description": "Installer package preview prohibited."
    },
    ".bat": {
        "mime": "text/x-bat",
        "category": "Batch script",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.BLOCKED_BINARY.value,
        "description": "Shell script execution prohibited."
    },
    ".cmd": {
        "mime": "text/x-bat",
        "category": "Batch script",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.BLOCKED_BINARY.value,
        "description": "Shell script execution prohibited."
    },
    ".ps1": {
        "mime": "text/x-powershell",
        "category": "PowerShell script",
        "mode": PreviewMode.UNSUPPORTED.value,
        "renderer": "none",
        "enabled": False,
        "security": PreviewSecurityPolicy.BLOCKED_BINARY.value,
        "description": "Script execution prohibited."
    }
}

# Magic Signatures for MIME Spoofing Protection (Section 7A.12)
MAGIC_SIGNATURES: Dict[str, bytes] = {
    "PE_EXECUTABLE": b"MZ",
    "PNG": b"\x89PNG\r\n\x1a\n",
    "JPEG": b"\xff\xd8\xff",
    "GIF": b"GIF8",
    "PDF": b"%PDF-",
    "ZIP": b"PK\x03\x04",
    "BMP": b"BM"
}

def detect_mime_spoofing(file_path: Path, declared_ext: str) -> Optional[str]:
    """
    Inspects leading magic bytes to ensure dangerous executables are not disguised
    under benign extensions like .png, .txt, or .docx.
    Returns error reason if spoofed, or None if safe.
    """
    if not file_path.exists() or file_path.stat().st_size < 4:
        return None

    try:
        with open(file_path, "rb") as f:
            header = f.read(16)

        # Check for disguised PE executable (MZ header)
        if header.startswith(MAGIC_SIGNATURES["PE_EXECUTABLE"]):
            if declared_ext.lower() not in (".exe", ".dll", ".sys"):
                return f"DANGEROUS_MIME_SPOOFING: File contains PE executable header (MZ) disguised as {declared_ext}"

        # Check if claimed PNG is actually valid PNG
        if declared_ext.lower() == ".png" and not header.startswith(MAGIC_SIGNATURES["PNG"]):
            return "MIME_SIGNATURE_MISMATCH: Declared .png file does not start with standard PNG header"

        # Check if claimed PDF is actually valid PDF
        if declared_ext.lower() == ".pdf" and not header.startswith(MAGIC_SIGNATURES["PDF"]):
            return "MIME_SIGNATURE_MISMATCH: Declared .pdf file does not start with %PDF- header"

        return None
    except Exception as ex:
        return f"HEADER_INSPECTION_ERROR: {str(ex)}"
