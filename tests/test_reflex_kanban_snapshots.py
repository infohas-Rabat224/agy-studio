"""
Tests for Vision Reflex, Kanban Board, and Time-Machine Rollback.
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

class ReflexKanbanSnapshotsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="agy_features_test_"))
        cls.orig_config_file = getattr(app.state, "config_file", None)
        cls.test_config = cls.temp_dir / "config.json"
        import json
        with open(cls.test_config, "w", encoding="utf-8") as f:
            json.dump({"workspace": str(cls.temp_dir)}, f)
        app.state.config_file = cls.test_config
        app.state.default_workspace = str(cls.temp_dir)

    @classmethod
    def tearDownClass(cls):
        if cls.orig_config_file:
            app.state.config_file = cls.orig_config_file

    def test_01_kanban_board_and_lifecycle(self):
        # 1. Get Board
        res = self.client.get("/api/kanban/board")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("ready", data["columns"])
        self.assertIn("in_progress", data["columns"])
        self.assertTrue(len(data["cards"]) >= 1)

        # 2. Create Card
        res_create = self.client.post("/api/kanban/card/create", json={
            "title": "Test Kanban Integration",
            "description": "Integration test card",
            "column": "ready",
            "priority": "HIGH",
            "assigned_agent": "Antigravity"
        })
        self.assertEqual(res_create.status_code, 200)
        card_id = res_create.json()["card"]["id"]

        # 3. Move Card
        res_move = self.client.post("/api/kanban/card/move", json={
            "card_id": card_id,
            "target_column": "in_progress"
        })
        self.assertEqual(res_move.status_code, 200)
        self.assertEqual(res_move.json()["card"]["column"], "in_progress")

        # 4. Update Card
        res_update = self.client.post("/api/kanban/card/update", json={
            "card_id": card_id,
            "progress": 75,
            "thinking_trace": "Testing in progress..."
        })
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()["card"]["progress"], 75)

        # 5. Execute Next
        res_exec = self.client.post("/api/kanban/execute-next")
        self.assertEqual(res_exec.status_code, 200)

        # 6. Delete Card
        res_del = self.client.post("/api/kanban/card/delete", json={"card_id": card_id})
        self.assertEqual(res_del.status_code, 200)

    def test_02_snapshot_and_rollback_lifecycle(self):
        # Create dummy file in test workspace
        sample_file = self.temp_dir / "app_version.txt"
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("Version 1.0.0 Original")

        # 1. Create Snapshot
        res_snap = self.client.post("/api/snapshots/create", json={"label": "Tour #1 Original"})
        self.assertEqual(res_snap.status_code, 200)
        snap_data = res_snap.json()
        snap_id = snap_data["snapshot"]["id"]
        self.assertTrue(snap_data["snapshot"]["files_count"] >= 1)

        # 2. List Snapshots
        res_list = self.client.get("/api/snapshots/list")
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(len(res_list.json()["snapshots"]) >= 1)

        # 3. Modify File (simulate agent regressions or code change)
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("Version 2.0.0 Broken Changes")

        # 4. Diff against Snapshot
        res_diff = self.client.get(f"/api/snapshots/diff?snapshot_id={snap_id}")
        self.assertEqual(res_diff.status_code, 200)
        diff_data = res_diff.json()
        self.assertEqual(diff_data["status"], "success")
        self.assertIn("app_version.txt", diff_data["modified_files"])
        self.assertIn("Version 1.0.0", diff_data["diffs"]["app_version.txt"])

        # 5. Rollback 1-Click
        res_rb = self.client.post("/api/snapshots/rollback", json={"snapshot_id": snap_id})
        self.assertEqual(res_rb.status_code, 200)
        self.assertTrue(res_rb.json()["restored_count"] >= 1)

        # Verify file content is restored
        with open(sample_file, "r", encoding="utf-8") as f:
            restored_content = f.read()
        self.assertEqual(restored_content, "Version 1.0.0 Original")

    def test_03_vision_reflex_audit(self):
        # Create small test HTML
        html_file = self.temp_dir / "test_preview.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><head><title>Test</title></head><body><div style='width: 3000px;'>Big overflow</div></body></html>")

        res = self.client.post("/api/vision-reflex/audit", json={
            "target": str(html_file),
            "viewport": "desktop"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn(data["status"], ["success", "warning"])
        self.assertTrue("score" in data)
        self.assertTrue("grade" in data)
        self.assertTrue("issues" in data)

    def test_04_vision_reflex_autofix_loop(self):
        # Create HTML with overflow defect
        html_file = self.temp_dir / "overflow_test.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><head><title>Overflow</title></head><body><div style='width: 3500px;'>Wide Div</div></body></html>")

        # 1. Audit before fix
        res_audit = self.client.post("/api/vision-reflex/audit", json={
            "target": str(html_file),
            "viewport": "desktop"
        })
        self.assertEqual(res_audit.status_code, 200)
        patch_css = res_audit.json().get("auto_patch_css", "body { overflow-x: hidden !important; }")

        # 2. Apply Auto-Fix
        res_fix = self.client.post("/api/vision-reflex/auto-fix", json={
            "target_file": str(html_file),
            "css_patch": patch_css,
            "viewport": "desktop"
        })
        self.assertEqual(res_fix.status_code, 200)
        fix_data = res_fix.json()
        self.assertEqual(fix_data["status"], "success")
        self.assertTrue(fix_data["new_score"] >= 80)
        self.assertIn("after_screenshot_url", fix_data)

if __name__ == "__main__":
    unittest.main()
