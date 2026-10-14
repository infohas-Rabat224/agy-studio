import sys
import os
import time
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.agent_adapters import (
    AgentRegistry, OrchestratorEngine, AgentStatus, CapabilityStatus,
    TaskExecutionRequest, TaskExecutionResult
)

class OrchestratorIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="agy_integration_"))
        cls.data_dir = cls.temp_dir / "data"
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        cls.registry = AgentRegistry(cls.data_dir, probe_ttl_seconds=86400)
        cls.orchestrator = OrchestratorEngine(cls.registry, cls.data_dir, probe_ttl_seconds=86400)
        
        # Initial discovery
        cls.registry.discover_all()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.temp_dir), ignore_errors=True)

    def test_01_antigravity_execution(self):
        """TEST 1: Antigravity executes a coding task."""
        print("\n--- INTEGRATION TEST 1: Antigravity Execution ---")
        # Verify Antigravity operational probe
        verified = self.registry.verify_agent("agy")
        self.assertEqual(verified["status"], AgentStatus.OPERATIONAL.value)
        
        ws = self.temp_dir / "task_agy"
        ws.mkdir(parents=True, exist_ok=True)
        
        rec = self.orchestrator.execute_task(
            task_id="int_task_1_agy",
            prompt="Respond with exactly AGY_AGENT_TEST_OK",
            role="CODER",
            workspace=ws,
            preferred_agent="agy",
            allow_fallback=False
        )
        self.assertEqual(rec["primary_agent"], "agy")
        self.assertEqual(rec["exit_code"], 0)
        self.assertTrue(rec["success"])
        self.assertIn("AGY_AGENT_TEST_OK", rec["stdout"])
        print(f"[TEST 1 PASS] Antigravity executed successfully in {rec['duration_ms']}ms (Exit: 0)")

    def test_02_opencode_execution(self):
        """TEST 2: OpenCode executes a coding task."""
        print("\n--- INTEGRATION TEST 2: OpenCode Execution ---")
        verified = self.registry.verify_agent("opencode")
        self.assertEqual(verified["status"], AgentStatus.OPERATIONAL.value)
        
        ws = self.temp_dir / "task_opencode"
        ws.mkdir(parents=True, exist_ok=True)
        
        rec = self.orchestrator.execute_task(
            task_id="int_task_2_opencode",
            prompt="Respond with exactly AGY_AGENT_TEST_OK",
            role="CODER",
            workspace=ws,
            preferred_agent="opencode",
            allow_fallback=False
        )
        self.assertEqual(rec["primary_agent"], "opencode")
        self.assertEqual(rec["exit_code"], 0)
        self.assertTrue(rec["success"])
        self.assertIn("AGY_AGENT_TEST_OK", rec["stdout"])
        print(f"[TEST 2 PASS] OpenCode executed successfully in {rec['duration_ms']}ms (Exit: 0)")

    def test_03_hermes_provider_execution(self):
        """TEST 3: Hermes successfully executes through an operational provider (gemini)."""
        print("\n--- INTEGRATION TEST 3: Hermes Provider Execution ---")
        # Verify Hermes using gemini provider
        verified = self.registry.verify_agent("hermes", provider_id="gemini")
        if verified["status"] != AgentStatus.OPERATIONAL.value:
            self.skipTest(f"Hermes is not operational (status={verified['status']}): {verified.get('last_probe_error')}")
        self.assertEqual(verified["status"], AgentStatus.OPERATIONAL.value)
        self.assertEqual(verified.get("active_provider"), "gemini")
        
        ws = self.temp_dir / "task_hermes"
        ws.mkdir(parents=True, exist_ok=True)
        
        rec = self.orchestrator.execute_task(
            task_id="int_task_3_hermes",
            prompt="Respond with exactly AGY_AGENT_TEST_OK",
            role="CODER",
            workspace=ws,
            preferred_agent="hermes",
            allow_fallback=False
        )
        self.assertEqual(rec["primary_agent"], "hermes")
        self.assertEqual(rec["exit_code"], 0)
        self.assertTrue(rec["success"])
        self.assertIn("AGY_AGENT_TEST_OK", rec["stdout"])
        print(f"[TEST 3 PASS] Hermes + gemini provider executed in {rec['duration_ms']}ms (Exit: 0)")

    def test_04_tty_only_cli_classification(self):
        """TEST 6: Unsupported TTY-only CLIs are correctly classified and not falsely executed."""
        print("\n--- INTEGRATION TEST 6: TTY-Only CLI Classification ---")
        cline = self.registry.get_agent("cline")
        self.assertIsNotNone(cline)
        self.assertEqual(cline["status"], AgentStatus.AVAILABLE.value)
        self.assertEqual(cline["capabilities"].get("non_interactive"), CapabilityStatus.UNSUPPORTED.value)
        
        qwen = self.registry.get_agent("qwen")
        self.assertIsNotNone(qwen)
        self.assertEqual(qwen["status"], AgentStatus.AVAILABLE.value)
        self.assertEqual(qwen["capabilities"].get("non_interactive"), CapabilityStatus.UNSUPPORTED.value)

        # Attempting to select cline for a non_interactive execution must never select cline
        sel, dec = self.orchestrator.select_agent(
            role="CODER",
            required_capabilities=["non_interactive"],
            preferred_agent="cline"
        )
        if sel:
            self.assertNotEqual(sel.id, "cline")
        cline_rej = next((r for r in dec.rejected_candidates if r["agent_id"] == "cline"), None)
        self.assertIsNotNone(cline_rej)
        self.assertTrue(
            "OPERATIONAL" in cline_rej["reason"] or "Missing required verified capabilities" in cline_rej["reason"]
        )
        print(f"[TEST 6 PASS] TTY-only CLIs correctly classified and rejected: {cline_rej['reason']}")

    def test_05_failover_execution(self):
        """TEST 8: Primary agent fails -> operational fallback agent executes."""
        print("\n--- INTEGRATION TEST 8: Failover Execution ---")
        ws = self.temp_dir / "task_failover"
        ws.mkdir(parents=True, exist_ok=True)
        
        # Create an agent that passes operational verification probe but fails on task execution
        dummy_script = self.temp_dir / "failing_agent.py"
        dummy_script.write_text(
            "import sys\n"
            "args_str = ' '.join(sys.argv)\n"
            "if '--version' in sys.argv:\n"
            "    print('v1.0')\n"
            "    sys.exit(0)\n"
            "elif 'Respond with exactly AGY_AGENT_TEST_OK' in args_str:\n"
            "    print('AGY_AGENT_TEST_OK')\n"
            "    sys.exit(0)\n"
            "else:\n"
            "    sys.exit(42)\n",
            encoding="utf-8"
        )
        
        self.registry.add_custom_agent(
            name="Failing Primary",
            command="fail_primary",
            custom_path=str(dummy_script),
            roles=["CODER"]
        )
        # Manually verify so it can be selected as primary
        fid = "custom_fail_primary"
        self.registry.verify_agent(fid)
        
        # Ensure operational agents are available for fallback
        self.registry.verify_agent("agy")
        self.registry.verify_agent("opencode")

        rec = self.orchestrator.execute_task(
            task_id="int_task_8_failover",
            prompt="Write a python comment # failover test",
            role="CODER",
            workspace=ws,
            preferred_agent=fid,
            allow_fallback=True
        )
        self.assertEqual(rec["primary_agent"], fid)
        self.assertTrue(rec["fallback_used"])
        self.assertIn(rec["fallback_agent"], ["agy", "opencode"])
        self.assertTrue(rec["success"])
        self.assertEqual(rec["failover_chain"], [fid, rec["fallback_agent"]])
        print(f"[TEST 8 PASS] Failover succeeded: {fid} (Exit 42) -> {rec['fallback_agent']} (Exit 0)")
        
        self.registry.delete_custom_agent(fid)

    def test_06_restart_persistence(self):
        """TEST 10: Restart Agy Studio -> all evidence and configuration persist correctly."""
        print("\n--- INTEGRATION TEST 10: Restart Persistence ---")
        # Save state and reload in a new registry instance pointing to the same data directory
        restarted_registry = AgentRegistry(self.data_dir, probe_ttl_seconds=86400)
        restarted_orchestrator = OrchestratorEngine(restarted_registry, self.data_dir, probe_ttl_seconds=86400)
        
        agy = restarted_registry.get_agent("agy")
        self.assertIsNotNone(agy)
        self.assertEqual(agy["status"], AgentStatus.OPERATIONAL.value)
        self.assertIsNotNone(agy.get("operational_evidence"))
        
        # Verify orchestrator selects an operational CODER from persisted state without re-running probe
        sel, dec = restarted_orchestrator.select_agent(role="CODER", required_capabilities=["chat"])
        self.assertIsNotNone(sel)
        self.assertIn(sel.id, ["agy", "opencode"])
        print(f"[TEST 10 PASS] State and evidence persisted and reloaded successfully upon restart (selected: {sel.id})")

if __name__ == "__main__":
    unittest.main()
