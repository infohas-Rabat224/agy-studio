import sys
import os
import shutil
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path dynamically
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.agent_adapters import AgentRegistry, OrchestratorEngine, AgentStatus

class PortabilityTest(unittest.TestCase):
    def test_portable_runtime_execution(self):
        """
        TEST 11: Simulate running Agy Studio from a completely different portable directory.
        No absolute developer path should be hardcoded or required.
        """
        print("\n--- PORTABLE TEST 11: Relocatable Runtime Execution ---")
        portable_root = Path(tempfile.mkdtemp(prefix="Portable_AgyStudio_"))
        try:
            portable_data = portable_root / "data"
            portable_data.mkdir(parents=True, exist_ok=True)
            
            # Initialize registry and orchestrator pointing to the new portable location
            portable_registry = AgentRegistry(portable_data)
            portable_orchestrator = OrchestratorEngine(portable_registry, portable_data)
            
            # Dynamic discovery on host system
            agents = portable_registry.discover_all()
            self.assertGreater(len(agents), 0)
            
            # Check agy or opencode discovered
            agy = portable_registry.get_agent("agy")
            self.assertIsNotNone(agy)
            self.assertIn(agy["status"], [AgentStatus.AVAILABLE.value, AgentStatus.READY.value, AgentStatus.OPERATIONAL.value])
            print(f"[TEST 11 PASS] Discovered {len(agents)} agents in portable environment {portable_root}")
        finally:
            shutil.rmtree(str(portable_root), ignore_errors=True)

    def test_path_removal_leads_to_not_installed(self):
        """
        TEST 12: When an executable is not found in PATH or standard user directories,
        it must be classified as NOT_INSTALLED.
        """
        print("\n--- PORTABLE TEST 12: Missing CLI Discovered as NOT_INSTALLED ---")
        portable_root = Path(tempfile.mkdtemp(prefix="Agy_NotInstalled_"))
        try:
            data_dir = portable_root / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            registry = AgentRegistry(data_dir)
            
            # Register a non-existent fake CLI
            res = registry.add_custom_agent(
                name="Fictional Agent",
                command="non_existent_binary_xyz_12345",
                custom_path="C:\\non_existent_folder\\fake.exe"
            )
            aid = res["id"]
            
            # Run discovery
            ag = registry.get_agent(aid)
            self.assertEqual(ag["status"], AgentStatus.NOT_INSTALLED.value)
            print(f"[TEST 12 PASS] Non-existent binary correctly classified as NOT_INSTALLED: {ag['status']}")
            
            registry.delete_custom_agent(aid)
        finally:
            shutil.rmtree(str(portable_root), ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
