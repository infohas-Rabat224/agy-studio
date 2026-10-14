"""
Image Processor for Agy Studio.
Handles real validation and metadata extraction for PNG, JPG/JPEG, WEBP, BMP, GIF, TIFF.
Generates preview thumbnails safely using Pillow.
"""

import io
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from .models import ArtifactMetadata, ArtifactExtraction, ExtractionStatus

SUPPORTED_IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"
}

class ImageProcessor:
    """
    Validates images, calculates dimensions, and generates previews.
    """

    @classmethod
    def process_image(cls, file_path: Path) -> Tuple[ArtifactMetadata, ArtifactExtraction, Optional[str]]:
        """
        Inspects image file and extracts real dimensions and format.
        Returns (metadata, extraction, preview_path).
        """
        metadata = ArtifactMetadata()
        extraction = ArtifactExtraction()
        preview_path = str(file_path)

        try:
            from PIL import Image
        except ImportError:
            extraction.status = ExtractionStatus.EXTRACTOR_UNAVAILABLE
            extraction.extractor = "pillow_missing"
            extraction.errors.append("Pillow (PIL) is not installed in runtime")
            return metadata, extraction, preview_path

        try:
            with Image.open(str(file_path)) as img:
                img.verify() # Verify integrity

            # Reopen to read dimensions and mode after verify()
            with Image.open(str(file_path)) as img:
                metadata.width = img.width
                metadata.height = img.height
                metadata.extra["format"] = img.format
                metadata.extra["mode"] = img.mode

                # If format is TIFF or BMP or massive, generate a lightweight web PNG thumbnail
                ext = file_path.suffix.lower()
                if ext in (".tiff", ".tif", ".bmp") or img.width > 2560 or img.height > 2560:
                    thumb_dir = file_path.parent / "previews"
                    thumb_dir.mkdir(exist_ok=True)
                    thumb_path = thumb_dir / f"{file_path.stem}_thumb.png"
                    if not thumb_path.exists():
                        copy_img = img.copy()
                        copy_img.thumbnail((1280, 1280))
                        copy_img.save(str(thumb_path), format="PNG")
                    preview_path = str(thumb_path)

            extraction.status = ExtractionStatus.TEXT_EXTRACTED
            extraction.extractor = "pillow_image_inspector"
        except Exception as ex:
            extraction.status = ExtractionStatus.FAILED
            extraction.errors.append(f"Image decode error: {ex}")
            extraction.extractor = "pillow_image_inspector"

        return metadata, extraction, preview_path
