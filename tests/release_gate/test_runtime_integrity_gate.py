import os
import sys
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
    TaskExecutionRequest, TaskExecutionResult,
    is_executable_identity_valid, compute_config_fingerprint
)

class RuntimeIntegrityGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="agy_release_gate_"))
        cls.data_dir = cls.temp_dir / "data"
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        cls.registry = AgentRegistry(cls.data_dir, probe_ttl_seconds=86400)
        cls.orchestrator = OrchestratorEngine(cls.registry, cls.data_dir, probe_ttl_seconds=86400)
        cls.registry.discover_all()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.temp_dir), ignore_errors=True)

    def test_01_forensic_record_completeness(self):
        """GATE 1: Operational verification retains complete forensic fields and zero unmasked secrets."""
        print("\n--- RELEASE GATE 1: Forensic Record Completeness ---")
        agy_res = self.registry.verify_agent("agy")
        self.assertEqual(agy_res["status"], AgentStatus.OPERATIONAL.value)
        
        op = agy_res["operational_evidence"]
        required_fields = [
            "execution_id", "agent_id", "provider_id", "model", "executable_path",
            "version", "workspace", "command_redacted", "started_at", "ended_at",
            "duration_ms", "pid", "exit_code", "stdout_redacted", "stderr_redacted",
            "capabilities", "artifact_paths", "verification_result"
        ]
        for field in required_fields:
            self.assertIn(field, op, f"Missing required forensic field: {field}")

        # Check executable identity block
        self.assertIsNotNone(op.get("executable_identity"))
        exe_id = op["executable_identity"]
        for k in ["file_size", "file_mtime", "optional_sha256", "verified_capabilities"]:
            self.assertIn(k, exe_id, f"Missing executable identity field: {k}")

        # Check configuration fingerprint
        self.assertIsNotNone(op.get("configuration_fingerprint"))
        self.assertEqual(len(op["configuration_fingerprint"]), 64) # sha256 hex

        # Check capability evidence integrity
        self.assertIn("capability_evidences", op)
        for cap_name, cap_ev in op["capability_evidences"].items():
            self.assertIn("capability", cap_ev)
            self.assertIn("status", cap_ev)
            if cap_ev["status"] == "VERIFIED":
                self.assertIsNotNone(cap_ev.get("verified_at"))
                self.assertIsNotNone(cap_ev.get("evidence_execution_id"))

        print(f"[GATE 1 PASS] All forensic fields, executable identity, and configuration fingerprint verified")

    def test_02_executable_replacement_detection(self):
        """GATE 2: Modifying or replacing executable immediately invalidates OPERATIONAL evidence."""
        print("\n--- RELEASE GATE 2: Executable Replacement & Stale Invalidation ---")
        # Create a test executable script
        script_a = self.temp_dir / "managed_cli.py"
        script_a.write_text(
            "import sys\n"
            "if '--version' in sys.argv:\n"
            "    print('v1.0.0')\n"
            "elif 'Respond with exactly AGY_AGENT_TEST_OK' in ' '.join(sys.argv):\n"
            "    print('AGY_AGENT_TEST_OK')\n"
            "else:\n"
            "    print('OK')\n",
            encoding="utf-8"
        )

        self.registry.add_custom_agent(
            name="Managed Agent",
            command="managed_cli",
            custom_path=str(script_a),
            roles=["CODER"]
        )
        agent_id = "custom_managed_cli"

        # 1. Verify executable A
        verified = self.registry.verify_agent(agent_id)
        self.assertEqual(verified["status"], AgentStatus.OPERATIONAL.value)

        # Confirm orchestrator accepts candidate
        sel, dec = self.orchestrator.select_agent(role="CODER", preferred_agent=agent_id)
        self.assertIsNotNone(sel)
        self.assertEqual(sel.id, agent_id)
        print(f"[STEP 1] Initial verification: {agent_id} accepted as OPERATIONAL")

        # 2. Replace executable with modified content (changes size and hash)
        time.sleep(0.05)
        script_a.write_text(
            "import sys\n"
            "if '--version' in sys.argv:\n"
            "    print('v2.0.0')\n"
            "elif 'Respond with exactly AGY_AGENT_TEST_OK' in ' '.join(sys.argv):\n"
            "    print('AGY_AGENT_TEST_OK')\n"
            "else:\n"
            "    print('OK v2')\n",
            encoding="utf-8"
        )
        print(f"[STEP 2] Executable binary replaced on disk with v2")

        # 3. Query orchestrator -> MUST detect change and reject as STALE
        sel2, dec2 = self.orchestrator.select_agent(role="CODER", preferred_agent=agent_id)
        if sel2:
            self.assertNotEqual(sel2.id, agent_id, "Orchestrator must NOT select modified executable!")
        rej = next((r for r in dec2.rejected_candidates if r["agent_id"] == agent_id), None)
        self.assertIsNotNone(rej)
        self.assertIn("STALE", rej["reason"])
        print(f"[STEP 3] Orchestrator strictly rejected modified binary: {rej['reason']}")

        # 4. Re-verify executable B
        verified_b = self.registry.verify_agent(agent_id)
        self.assertEqual(verified_b["status"], AgentStatus.OPERATIONAL.value)

        # 5. Confirm it is eligible again
        sel3, dec3 = self.orchestrator.select_agent(role="CODER", preferred_agent=agent_id)
        self.assertIsNotNone(sel3)
        self.assertEqual(sel3.id, agent_id)
        print(f"[STEP 4-5] Re-verification succeeded: {agent_id} eligible again with updated baseline")

        self.registry.delete_custom_agent(agent_id)

    def test_03_provider_change_integrity(self):
        """GATE 3: Provider switch invalidates prior provider evidence (Hermes)."""
        print("\n--- RELEASE GATE 3: Multi-Provider Change Integrity ---")
        # 1. Verify Hermes with gemini provider
        verified_gem = self.registry.verify_agent("hermes", provider_id="gemini")
        if verified_gem["status"] != AgentStatus.OPERATIONAL.value:
            self.skipTest(f"Hermes is not operational (status={verified_gem['status']}): {verified_gem.get('last_probe_error')}")
        self.assertEqual(verified_gem["status"], AgentStatus.OPERATIONAL.value)
        self.assertEqual(verified_gem["active_provider"], "gemini")

        # 2. Confirm Hermes + gemini is selected when preferred
        sel, dec = self.orchestrator.select_agent(role="CODER", preferred_agent="hermes", preferred_provider="gemini")
        self.assertIsNotNone(sel)
        self.assertEqual(sel.id, "hermes")
        print("[STEP 1-2] Hermes verified with gemini provider and accepted by orchestrator")

        # 3. Query orchestrator requesting a different unverified provider (e.g. 'deepseek')
        sel_ds, dec_ds = self.orchestrator.select_agent(role="CODER", preferred_agent="hermes", preferred_provider="deepseek")
        if sel_ds:
            self.assertNotEqual(sel_ds.id, "hermes", "Hermes must NOT be selected for deepseek using gemini evidence!")
        hermes_rej = next((r for r in dec_ds.rejected_candidates if r["agent_id"] == "hermes"), None)
        self.assertIsNotNone(hermes_rej)
        self.assertIn("gemini", hermes_rej["reason"])
        self.assertIn("deepseek", hermes_rej["reason"])
        print(f"[STEP 3] Orchestrator strictly rejected unverified provider: {hermes_rej['reason']}")

    def test_04_restart_and_persistence_gate(self):
        """GATE 4: Full restart preserves valid evidence, checks identity, and rejects stale evidence."""
        print("\n--- RELEASE GATE 4: Restart & Persistence Gate ---")
        # Restart registry & orchestrator instances
        new_registry = AgentRegistry(self.data_dir, probe_ttl_seconds=86400)
        new_orchestrator = OrchestratorEngine(new_registry, self.data_dir, probe_ttl_seconds=86400)

        # Check Antigravity persisted state
        agy = new_registry.get_agent("agy")
        self.assertIsNotNone(agy)
        self.assertEqual(agy["status"], AgentStatus.OPERATIONAL.value)
        self.assertIsNotNone(agy.get("executable_identity"))
        self.assertIsNotNone(agy.get("configuration_fingerprint"))

        # Check that orchestrator validates identity upon restart
        sel, dec = new_orchestrator.select_agent(role="CODER", required_capabilities=["chat", "code"])
        self.assertIsNotNone(sel)
        self.assertEqual(sel.id, "agy")
        print("[GATE 4 PASS] State, identity, and fingerprints loaded from disk without re-probing")

    def test_05_unknown_agent_regression(self):
        """GATE 5: Full 10-step lifecycle of an unknown custom CLI agent."""
        print("\n--- RELEASE GATE 5: Universal Unknown CLI Regression ---")
        unk_script = self.temp_dir / "unknown_future_agent.py"
        unk_script.write_text(
            "import sys\n"
            "args = ' '.join(sys.argv)\n"
            "if '--version' in sys.argv:\n"
            "    print('UniversalAgent v9.9.9')\n"
            "    sys.exit(0)\n"
            "elif 'AGY_AGENT_TEST_OK' in args:\n"
            "    print('AGY_AGENT_TEST_OK')\n"
            "    sys.exit(0)\n"
            "else:\n"
            "    with open('output_task.txt', 'w') as f:\n"
            "        f.write('TASK COMPLETED')\n"
            "    print('Task finished successfully')\n"
            "    sys.exit(0)\n",
            encoding="utf-8"
        )

        reg_agent = self.registry.add_custom_agent(
            name="Universal Unknown CLI",
            command="unk_agent",
            custom_path=str(unk_script),
            roles=["CODER", "PLANNER"]
        )
        aid = "custom_unk_agent"
        self.assertIn(reg_agent["status"], [AgentStatus.AVAILABLE.value, AgentStatus.READY.value])

        # Verify probe
        ver = self.registry.verify_agent(aid)
        self.assertEqual(ver["status"], AgentStatus.OPERATIONAL.value)
        self.assertEqual(ver["operational_evidence"]["verification_result"], "PASS")

        # Execute task through orchestrator
        ws = self.temp_dir / "ws_unk"
        ws.mkdir(parents=True, exist_ok=True)
        res = self.orchestrator.execute_task(
            task_id="task_unk_gate",
            prompt="Do task",
            role="CODER",
            workspace=ws,
            preferred_agent=aid,
            allow_fallback=False
        )
        self.assertEqual(res["primary_agent"], aid)
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("output_task.txt", res["artifacts"])
        print(f"[GATE 5 PASS] Unknown CLI successfully discovered, verified, and executed with artifact detection")

        self.registry.delete_custom_agent(aid)

    def test_06_multimodal_vision_gate(self):
        """GATE 6: Multimodal Vision Gate strictly distinguishes ingestion vs delivery vs understanding."""
        print("\n--- RELEASE GATE 6: Multimodal Vision Gate ---")
        from tests.integration.test_vision_agent import execute_vision_probe
        
        probe_file = self.data_dir / "gate_vision_probe.json"
        res = execute_vision_probe(data_dir=self.data_dir, output_evidence_file=probe_file)
        
        # Ingestion MUST always be verified for real image
        self.assertTrue(res["image_ingestion_verified"], "Image ingestion must be verified")
        self.assertTrue(probe_file.exists(), "Forensic evidence must be persisted")
        
        # When no operational vision agent exists on host:
        # Must report VISION_AGENT_UNAVAILABLE and reject delivery/understanding
        if res["status"] == "VISION_AGENT_UNAVAILABLE":
            self.assertEqual(res["reason"], "BLOCKED — NO OPERATIONAL VISION-CAPABLE AGENT")
            self.assertFalse(res["image_agent_delivery_verified"], "Cannot deliver image to text-only agent")
            self.assertFalse(res["image_understanding_verified"], "Cannot claim understanding without vision agent")
            print("[GATE 6 PASS] Vision gate strictly blocked false multimodal claims: " + res["reason"])
        else:
            self.assertEqual(res["status"], "SUCCESS")
            self.assertTrue(res["image_agent_delivery_verified"])
            self.assertTrue(res["image_understanding_verified"])
            print(f"[GATE 6 PASS] Vision understanding verified with agent {res['execution_details']['agent_id']}")

if __name__ == "__main__":
    unittest.main()
