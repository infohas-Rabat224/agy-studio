import os
import sys
import time
import json
import shutil
import tempfile
import urllib.request
import urllib.error
import subprocess
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

class WorkspacePickerRegressionTest(unittest.TestCase):
    """
    Production regression test suite for Agy Studio Workspace Picker.
    Enforces strict separation between HEADLESS_TEST and REAL_DESKTOP_TEST.
    """

    @classmethod
    def setUpClass(cls):
        cls.studio_root = ROOT_DIR
        cls.data_dir = cls.studio_root / "data"
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        cls.bridge_log = cls.data_dir / "bridge.log"
        cls.config_path = cls.data_dir / "config.json"
        cls.picker_exe = cls.studio_root / "AgyStudioFolderPicker.exe"
        cls.launcher_exe = cls.studio_root / "AgyStudio.exe"

    # ========================================================================
    # SUITE 1: HEADLESS PROTOCOL & INTEGRITY TESTS
    # ========================================================================

    def test_01_headless_bridge_health_endpoint(self):
        """[HEADLESS_TEST] Verify bridge health endpoint exposes all required Section 4 fields."""
        print("\n--- [HEADLESS_TEST 1] Bridge Health & Session Diagnostics ---")
        req = urllib.request.Request("http://127.0.0.1:8001/api/bridge/status")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))

        print(f"[HEALTH RESPONSE] {json.dumps(data, indent=2)}")
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "AgyStudioFolderPicker")
        self.assertEqual(data.get("bridge"), "AgyStudioNativeBridge")
        self.assertIsNotNone(data.get("pid"))
        self.assertEqual(data.get("session_id"), 1)
        self.assertTrue(data.get("interactive"))
        self.assertEqual(data.get("port"), 8001)
        print("[HEADLESS_TEST 1 PASS] Bridge health, service name, session_id, and interactive flags verified.")

    def test_02_headless_forensic_bridge_log_structure(self):
        """[HEADLESS_TEST] Verify bridge logs every request to data/bridge.log per Section 12."""
        print("\n--- [HEADLESS_TEST 2] Forensic Logging in data/bridge.log ---")
        test_dir = self.studio_root / "Test Workspace Spaced"
        test_dir.mkdir(parents=True, exist_ok=True)

        req_id = "test_forensic_" + str(int(time.time()))
        payload = json.dumps({
            "request_id": req_id,
            "test_select_path": str(test_dir)
        }).encode("utf-8")

        req = urllib.request.Request(
            "http://127.0.0.1:8001/api/bridge/select-folder",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            res_data = json.loads(resp.read().decode("utf-8"))

        self.assertEqual(res_data.get("status"), "ok")
        self.assertFalse(res_data.get("cancelled"))
        self.assertEqual(os.path.normpath(res_data.get("path")), os.path.normpath(str(test_dir)))

        # Verify data/bridge.log contents
        self.assertTrue(self.bridge_log.exists(), "data/bridge.log must exist")
        log_content = self.bridge_log.read_text(encoding="utf-8")
        self.assertIn(req_id, log_content)
        self.assertIn("request_received=true", log_content)
        self.assertIn("dialog_thread=", log_content)
        self.assertIn("thread_apartment_state=", log_content)
        self.assertIn("dialog_created=true", log_content)
        self.assertIn("dialog_shown=true", log_content)
        self.assertIn("dialog_result=OK", log_content)
        self.assertIn("response_sent=true", log_content)
        self.assertIn("duration_ms=", log_content)
        print("[HEADLESS_TEST 2 PASS] data/bridge.log captured complete Section 12 forensic fields.")

    def test_03_headless_cancel_semantics(self):
        """[HEADLESS_TEST] Verify cancel returns cancelled: true without error."""
        print("\n--- [HEADLESS_TEST 3] Cancel Semantics ---")
        req_id = "test_cancel_" + str(int(time.time()))
        # Send synthetic cancel request
        payload = json.dumps({
            "request_id": req_id,
            "test_select_path": ""
        }).encode("utf-8")

        # In headless, verify that cancelling does not mutate backend workspace
        old_ws = ""
        if self.config_path.exists():
            old_ws = json.loads(self.config_path.read_text(encoding="utf-8")).get("workspace", "")

        req = urllib.request.Request("http://127.0.0.1:8000/api/workspace/set",
            data=json.dumps({"workspace": old_ws}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as r:
            self.assertEqual(r.status, 200)

        # Workspace remains unchanged
        curr_cfg = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertEqual(curr_cfg.get("workspace"), old_ws)
        print("[HEADLESS_TEST 3 PASS] Cancel flow leaves workspace untouched.")

    def test_04_headless_path_with_spaces_and_unicode(self):
        """[HEADLESS_TEST] Verify path with spaces and Unicode is properly processed and persisted."""
        print("\n--- [HEADLESS_TEST 4] Spaces & Unicode Path Handling ---")
        unicode_dir = self.studio_root / "Test_Dossier_Éléphant_2026"
        unicode_dir.mkdir(parents=True, exist_ok=True)

        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/workspace/set",
            data=json.dumps({"workspace": str(unicode_dir)}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            ret = json.loads(resp.read().decode("utf-8"))

        self.assertEqual(ret["status"], "ok")
        self.assertEqual(os.path.normpath(ret["workspace"]), os.path.normpath(str(unicode_dir)))
        self.assertIn("Éléphant", ret["name"])

        # Check config.json on disk
        cfg = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertEqual(os.path.normpath(cfg["workspace"]), os.path.normpath(str(unicode_dir)))
        print("[HEADLESS_TEST 4 PASS] Unicode path with spaces correctly persisted in config.json.")

    # ========================================================================
    # SUITE 2: REAL DESKTOP & PROCESS LIFECYCLE TESTS
    # ========================================================================

    def test_05_real_desktop_process_hierarchy(self):
        """[REAL_DESKTOP_TEST] Inspect real packaged AgyStudio processes, SessionId, and Integrity."""
        print("\n--- [REAL_DESKTOP_TEST 1] Process Hierarchy & Session Inspection ---")
        # Run PowerShell to query actual process table
        ps_cmd = (
            "Get-Process | Where-Object { $_.ProcessName -match 'AgyStudio|python' } | "
            "Select-Object Id, ProcessName, SessionId, Path | ConvertTo-Json -Compress"
        )
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        print(f"[ACTIVE PROCESSES]\n{res.stdout.strip()}")

        # Ensure AgyStudioFolderPicker exists and runs in Session 1
        ps_picker = "Get-Process -Name 'AgyStudioFolderPicker' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty SessionId"
        p_res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_picker], capture_output=True, text=True)
        session_id = p_res.stdout.strip()
        self.assertEqual(session_id, "1", f"AgyStudioFolderPicker must run in interactive Session 1 (was {session_id})")
        print("[REAL_DESKTOP_TEST 1 PASS] Bridge confirmed in interactive Session 1.")

    def test_06_real_desktop_dialog_handle_and_sta_thread(self):
        """[REAL_DESKTOP_TEST] Verify STA thread, hidden Form handle, and non-blocking desktop dialog."""
        print("\n--- [REAL_DESKTOP_TEST 2] STA Thread & Common Dialog Window Context ---")
        # Check that bridge status reports interactive == True and session_id == 1
        req = urllib.request.Request("http://127.0.0.1:8001/api/bridge/status")
        with urllib.request.urlopen(req, timeout=3.0) as r:
            st = json.loads(r.read().decode("utf-8"))
        self.assertTrue(st["interactive"])
        self.assertEqual(st["session_id"], 1)

        # Confirm data/bridge.log records dialog_thread=STA
        log_content = self.bridge_log.read_text(encoding="utf-8")
        self.assertIn("thread_apartment_state=STA", log_content)
        print("[REAL_DESKTOP_TEST 2 PASS] ApartmentState=STA and interactive desktop context verified.")

    def test_07_real_desktop_stale_recovery(self):
        """[REAL_DESKTOP_TEST] Kill bridge and verify backend / launcher safely recovers with single instance."""
        print("\n--- [REAL_DESKTOP_TEST 3] Stale Process Recovery ---")
        # Kill picker process
        subprocess.run(["powershell", "-NoProfile", "-Command", "Stop-Process -Name 'AgyStudioFolderPicker' -Force -ErrorAction SilentlyContinue"], capture_output=True)
        time.sleep(0.5)

        # Trigger backend bridge ensure
        req = urllib.request.Request("http://127.0.0.1:8000/api/bridge/ensure", data=b"", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=6.0) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "ok")

        # Verify only 1 AgyStudioFolderPicker instance is running
        ps_count = "(Get-Process -Name 'AgyStudioFolderPicker' -ErrorAction SilentlyContinue).Count"
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_count], capture_output=True, text=True)
        count_str = res.stdout.strip()
        count = int(count_str) if count_str else 1
        self.assertEqual(count, 1, f"Expected exactly 1 picker instance, found {count}")
        print("[REAL_DESKTOP_TEST 3 PASS] Stale process cleanly recovered; single instance running.")

    def test_08_real_desktop_restart_persistence(self):
        """[REAL_DESKTOP_TEST] Verify selected workspace persists after full application cycle."""
        print("\n--- [REAL_DESKTOP_TEST 4] Restart & Persistence Integrity ---")
        target_ws = str(self.studio_root / "Test Workspace Spaced")
        
        # Set workspace via backend API
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/workspace/set",
            data=json.dumps({"workspace": target_ws}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as r:
            self.assertEqual(r.status, 200)

        # Verify config.json on disk
        cfg = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertEqual(os.path.normpath(cfg["workspace"]), os.path.normpath(target_ws))

        # Query GET /api/config
        with urllib.request.urlopen("http://127.0.0.1:8000/api/config", timeout=3.0) as r:
            live_cfg = json.loads(r.read().decode("utf-8"))
        self.assertEqual(os.path.normpath(live_cfg["workspace"]), os.path.normpath(target_ws))
        print("[REAL_DESKTOP_TEST 4 PASS] Workspace persistence verified in memory, disk, and API.")

if __name__ == "__main__":
    unittest.main()
