import sys
import os
import time
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path dynamically
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.agent_adapters import (
    AgentRegistry, OrchestratorEngine, AgentStatus, CapabilityStatus,
    TaskExecutionRequest, TaskExecutionResult, ExecutionProfile, ExecutionMode,
    kill_process_tree, redact_secrets
)

class UniversalAgentConformanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="agy_conformance_"))
        cls.data_dir = cls.temp_dir / "data"
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        cls.registry = AgentRegistry(cls.data_dir, probe_ttl_seconds=3600)
        cls.orchestrator = OrchestratorEngine(cls.registry, cls.data_dir, probe_ttl_seconds=3600)
        cls.unknown_script = ROOT_DIR / "tests" / "agent_conformance" / "unknown_agent.py"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.temp_dir), ignore_errors=True)

    def test_01_unknown_custom_cli_lifecycle(self):
        """
        MANDATORY REQUIREMENT 23:
        1. Register unknown agent
        2. Version test
        3. Capability probe
        4. Execute task
        5. Create artifact
        6. Capture output
        7. Cancel execution
        8. Persist evidence
        9. Remove agent
        10. Verify removal
        """
        print("\n--- TEST: Unknown Future CLI Conformance ---")
        
        # 1. Register unknown CLI
        reg_result = self.registry.add_custom_agent(
            name="Unknown Future Agent",
            command="unknown_agent",
            custom_path=str(self.unknown_script),
            version_args=["--version"],
            test_args=["-p", "{prompt}"],
            timeout=30,
            roles=["CODER", "PLANNER"],
            declared_capabilities={"chat": True, "code": True, "file_write": True}
        )
        agent_id = reg_result["id"]
        self.assertIn("custom_unknown_agent", agent_id)
        print(f"[STEP 1] Registered: {agent_id}")

        # 2. Version test
        adapter = self.registry.get_adapter(agent_id)
        self.assertIsNotNone(adapter)
        ok, version, ev = adapter.get_version(str(self.unknown_script))
        self.assertTrue(ok)
        self.assertIn("UnknownAgent CLI v3.1.0", version)
        self.assertEqual(ev.exit_code, 0)
        print(f"[STEP 2] Version probe: {version} in {ev.duration_ms}ms")

        # 3. Capability probe
        probe_ok, op_ev = adapter.probe(str(self.unknown_script), timeout=10)
        self.assertTrue(probe_ok)
        self.assertEqual(op_ev.actual_output, "AGY_AGENT_TEST_OK")
        self.assertEqual(op_ev.exit_code, 0)
        print(f"[STEP 3] Operational probe: PASS in {op_ev.duration_ms}ms")

        # Verify through registry (promotes to OPERATIONAL)
        verified_agent = self.registry.verify_agent(agent_id)
        self.assertEqual(verified_agent["status"], AgentStatus.OPERATIONAL.value)
        self.assertEqual(verified_agent["capabilities"]["chat"], CapabilityStatus.VERIFIED.value)
        self.assertEqual(verified_agent["capabilities"]["code"], CapabilityStatus.VERIFIED.value)
        self.assertEqual(verified_agent["capabilities"]["file_write"], CapabilityStatus.VERIFIED.value)
        print(f"[STEP 3b] Promoted to OPERATIONAL with verified capabilities")

        # 4 & 5 & 6. Execute task, create artifact, capture output
        task_ws = self.temp_dir / "workspace_unknown_task"
        task_ws.mkdir(parents=True, exist_ok=True)
        
        req = TaskExecutionRequest(
            task_id="conformance_unknown_exec",
            agent_id=agent_id,
            role="CODER",
            workspace=str(task_ws),
            prompt="write artifact please",
            required_capabilities=["code", "file_write"],
            timeout_seconds=15
        )
        res: TaskExecutionResult = adapter.execute(req)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.status, "SUCCESS")
        self.assertIn("Artifact created", res.stdout)
        
        # Verify artifact detection
        artifact_path = task_ws / "custom_output.txt"
        self.assertTrue(artifact_path.exists())
        self.assertIn("custom_output.txt", res.artifacts)
        print(f"[STEPS 4-6] Task execution: SUCCESS, Artifacts detected: {res.artifacts}")

        # 7. Cancel execution test
        t0 = time.time()
        import subprocess
        # Start a hanging process
        proc = subprocess.Popen(
            [sys.executable, str(self.unknown_script), "-p", "sleep 30"],
            cwd=str(task_ws)
        )
        cancel_ok = kill_process_tree(proc.pid)
        self.assertTrue(cancel_ok)
        time.sleep(0.3)
        self.assertIsNotNone(proc.poll())
        print(f"[STEP 7] Cancellation: Process {proc.pid} verified terminated")

        # 8. Persist evidence
        agents_data = self.registry._load_data().get("agents", {})
        self.assertIn(agent_id, agents_data)
        self.assertEqual(agents_data[agent_id]["status"], AgentStatus.OPERATIONAL.value)
        print(f"[STEP 8] Evidence persisted in agents.json")

        # 9 & 10. Remove agent and verify removal
        del_ok = self.registry.delete_custom_agent(agent_id)
        self.assertTrue(del_ok)
        fresh_data = self.registry._load_data().get("agents", {})
        self.assertNotIn(agent_id, fresh_data)
        self.assertIsNone(self.registry.get_adapter(agent_id))
        print(f"[STEPS 9-10] Removed custom agent and verified cleanup: PASS")

    def test_02_orchestrator_strict_filtering(self):
        """
        Verifies orchestrator enforces OPERATIONAL requirement,
        rejection reasons, role binding, and capabilities.
        """
        print("\n--- TEST: Orchestrator Strict Filtering ---")
        self.registry.discover_all()
        # Try selecting for a role with no operational agents in this fresh test registry
        selected, decision = self.orchestrator.select_agent(
            role="CODER",
            required_capabilities=["code"]
        )
        # None should be selected because none have been verified operational yet in this clean test registry
        self.assertIsNone(selected)
        self.assertGreater(len(decision.rejected_candidates), 0)
        for rej in decision.rejected_candidates:
            self.assertIn(rej["status"], [
                AgentStatus.NOT_INSTALLED.value,
                AgentStatus.AVAILABLE.value,
                AgentStatus.READY.value
            ])
            self.assertTrue(len(rej["reason"]) > 0)
        print(f"[ORCHESTRATOR] Verified strict rejection of unverified candidates: PASS")

    def test_03_secret_redaction(self):
        """Verifies API keys and secrets are masked."""
        raw = "Error with key sk-abcdef1234567890abcdef1234567890 and Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        masked = redact_secrets(raw)
        self.assertNotIn("sk-abcdef1234567890abcdef1234567890", masked)
        self.assertIn("sk-a****7890", masked)
        print(f"[SECURITY] Secret redaction: PASS")

    def test_04_stale_health_expiration(self):
        """Verifies orchestrator marks operational evidence STALE when TTL expires."""
        print("\n--- TEST: Stale Health Expiration ---")
        short_ttl_engine = OrchestratorEngine(self.registry, self.data_dir, probe_ttl_seconds=1)
        
        # Register and verify unknown agent
        reg_result = self.registry.add_custom_agent(
            name="Temporary Stale Agent",
            command="temp_stale",
            custom_path=str(self.unknown_script),
            roles=["CODER"]
        )
        aid = reg_result["id"]
        self.registry.verify_agent(aid)
        
        # Verify it is operational immediately
        agent_data = self.registry.get_agent(aid)
        self.assertEqual(agent_data["status"], AgentStatus.OPERATIONAL.value)
        
        # Sleep 2 seconds so verification age > 1s TTL
        time.sleep(2)
        
        # Orchestrator select with 1s TTL should reject it as STALE
        sel, dec = short_ttl_engine.select_agent(role="CODER", required_capabilities=["chat"])
        self.assertIsNone(sel)
        stale_rej = next((r for r in dec.rejected_candidates if r["agent_id"] == aid), None)
        self.assertIsNotNone(stale_rej)
        self.assertEqual(stale_rej["status"], AgentStatus.STALE.value)
        self.assertIn("Operational verification expired", stale_rej["reason"])
        print(f"[HEALTH] Stale expiration enforced: {stale_rej['reason']}")
        
        self.registry.delete_custom_agent(aid)

if __name__ == "__main__":
    unittest.main()
