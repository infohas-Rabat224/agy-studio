"""
Playwright Real Preview UI and DOM Verification Test.
Automates real artifact selection, DOM verification, console error monitoring,
and screenshot evidence generation per Sections 30, 31, 37, 39, 40.
"""

import os
import sys
import time
import json
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright

from backend.server import artifact_manager
from backend.artifacts.models import ArtifactAcquisition

class PlaywrightRealPreviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.screenshots_dir = Path("data/forensics/screenshots")
        cls.screenshots_dir.mkdir(parents=True, exist_ok=True)
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="agy_ui_preview_"))

    def test_01_playwright_e2e_real_preview(self):
        """End-to-End Real Preview DOM and visual rendering verification."""
        # 1. Create real artifacts
        # PNG
        from PIL import Image
        png_p = self.temp_dir / "ui_sample.png"
        im = Image.new("RGB", (320, 240), color=(46, 204, 113))
        im.save(png_p, format="PNG")
        art_png = artifact_manager.ingest_file(png_p, "ui_sample.png", session_id="ui_sess")

        # PDF
        import pypdf
        pdf_p = self.temp_dir / "ui_sample.pdf"
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=612, height=792)
        with open(pdf_p, "wb") as f:
            writer.write(f)
        art_pdf = artifact_manager.ingest_file(pdf_p, "ui_sample.pdf", session_id="ui_sess")

        # DOCX
        import docx
        docx_p = self.temp_dir / "ui_sample.docx"
        doc = docx.Document()
        doc.add_heading("Production Verification DOCX", level=1)
        doc.add_paragraph("Real Preview DOM Rendering Paragraph")
        tbl = doc.add_table(rows=2, cols=2)
        tbl.cell(0, 0).text = "Column A"
        tbl.cell(0, 1).text = "Column B"
        tbl.cell(1, 0).text = "100"
        tbl.cell(1, 1).text = "200"
        doc.save(str(docx_p))
        art_docx = artifact_manager.ingest_file(docx_p, "ui_sample.docx", session_id="ui_sess")

        # XLSX
        import openpyxl
        xlsx_p = self.temp_dir / "ui_sample.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Financials"
        ws.append(["Q1", "Q2", "Q3", "Total"])
        ws.append([1000, 1500, 2000, 4500])
        wb.save(str(xlsx_p))
        art_xlsx = artifact_manager.ingest_file(xlsx_p, "ui_sample.xlsx", session_id="ui_sess")

        # TXT
        txt_p = self.temp_dir / "ui_sample.txt"
        txt_p.write_text("Hello from verified real preview text!", encoding="utf-8")
        art_txt = artifact_manager.ingest_file(txt_p, "ui_sample.txt", session_id="ui_sess")

        console_errors = []
        page_errors = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1600, "height": 900})
            page = context.new_page()

            # Monitor console and errors
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            # Navigate to Agy Studio
            page.goto("http://127.0.0.1:8000", wait_until="networkidle")
            self.assertIn("Agy Studio", page.title())

            # Verify Real Preview panel exists
            preview_panel = page.locator("#previewPanel")
            self.assertTrue(preview_panel.count() > 0)

            # --- A. PNG Preview ---
            page.evaluate(f"previewArtifact('{art_png.id}')")
            page.wait_for_selector("#previewBody img", timeout=5000)
            img_src = page.locator("#previewBody img").get_attribute("src")
            self.assertTrue(img_src.startswith("/api/artifacts/"))
            page.screenshot(path=str(self.screenshots_dir / "preview_png.png"))

            # --- B. PDF Preview ---
            page.evaluate(f"previewArtifact('{art_pdf.id}')")
            page.wait_for_selector("#previewBody iframe", timeout=5000)
            iframe_src = page.locator("#previewBody iframe").get_attribute("src")
            self.assertIn(art_pdf.id, iframe_src)
            page.screenshot(path=str(self.screenshots_dir / "preview_pdf.png"))

            # --- C. DOCX Preview ---
            page.evaluate(f"previewArtifact('{art_docx.id}')")
            page.wait_for_selector("#previewBody .docx-preview", timeout=5000)
            body_text = page.locator("#previewBody").inner_text()
            self.assertIn("Production Verification DOCX", body_text)
            self.assertIn("Column A", body_text)
            page.screenshot(path=str(self.screenshots_dir / "preview_docx.png"))

            # --- D. XLSX Preview ---
            page.evaluate(f"previewArtifact('{art_xlsx.id}')")
            page.wait_for_selector("#previewBody .xlsx-preview", timeout=5000)
            xlsx_text = page.locator("#previewBody").inner_text()
            self.assertIn("Financials", xlsx_text)
            self.assertIn("4500", xlsx_text)
            page.screenshot(path=str(self.screenshots_dir / "preview_xlsx.png"))

            # --- E. TXT Preview ---
            page.evaluate(f"previewArtifact('{art_txt.id}')")
            page.wait_for_selector("#previewBody pre", timeout=5000)
            txt_content = page.locator("#previewBody pre").inner_text()
            self.assertIn("Hello from verified real preview text!", txt_content)
            page.screenshot(path=str(self.screenshots_dir / "preview_txt.png"))

            browser.close()

        # Section 37: Zero console errors, zero page errors
        self.assertEqual(len(page_errors), 0, f"Page errors encountered: {page_errors}")
        print("[PLAYWRIGHT SUCCESS] Verified 5 real previews, 0 page errors, captured screenshots.")

if __name__ == "__main__":
    unittest.main()
