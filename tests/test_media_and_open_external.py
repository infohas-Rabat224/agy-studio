"""
Integration test for Real Media Generation and External Application Launch.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.server import app

class MediaAndOpenExternalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="agy_media_test_"))
        app.state.default_workspace = str(cls.temp_dir)

    def test_01_real_media_generation(self):
        prompt = (
            "Till Assistant | Qatar Duty Free General Information Ref # 2600005S "
            "Location Qatar-Doha Closing Date: 2026-10-31 "
            "i need it as instgram post dimenssion and should not have logos also should be very realistic"
        )
        res = self.client.post("/api/media/generate", json={
            "prompt": prompt,
            "media_type": "image",
            "aspect_ratio": "1:1"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "created")
        self.assertEqual(data["dimensions"], "1080x1080")
        self.assertTrue(data["filename"].endswith(".png"))
        self.assertTrue(data["url"].startswith("/api/media/raw/"))

        # Verify real image file exists on disk
        from PIL import Image
        media_file = Path("C:/Agy Studio/data/media") / data["filename"]
        self.assertTrue(media_file.exists())
        with Image.open(media_file) as im:
            self.assertEqual(im.size, (1080, 1080))

    def test_02_open_file_external_resolves_media_and_workspace(self):
        # 1. Open media URL
        media_url = "/api/media/raw/image_till_assistant___qatar_du_1791538274.png"
        res_media = self.client.post("/api/file/open_external", json={"path": media_url})
        self.assertEqual(res_media.status_code, 200)
        self.assertIn(res_media.json()["status"], ["opened", "opened_explorer"])

        # 2. Open workspace file
        sample = self.temp_dir / "sample.txt"
        sample.write_text("Test external open")
        res_ws = self.client.post("/api/file/open_external", json={"path": "sample.txt"})
        self.assertEqual(res_ws.status_code, 200)
        self.assertIn(res_ws.json()["status"], ["opened", "opened_explorer"])

if __name__ == "__main__":
    unittest.main()
