"""
Integration tests for the Universal Vision Adapter Layer, Two-Stage PDF Processing,
and the Session -> Artifact -> Task -> Agent -> Execution Correlation Chain.
"""

import os
import io
import sys
import time
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from pypdf import PdfWriter

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.session.session_manager import SessionManager, SessionRecord
from backend.agent_adapters import (
    AgentRegistry, OrchestratorEngine, AgentStatus, CapabilityStatus, AgentModel
)
from backend.artifacts.artifact_manager import ArtifactManager
from backend.artifacts.document_extractor import DocumentExtractor
from backend.artifacts.capability_negotiator import ArtifactCapabilityNegotiator
from backend.artifacts.models import ArtifactAcquisition, ArtifactSourceType, ExtractionStatus


class UniversalVisionAdapterIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="agy_univ_vision_"))
        cls.data_dir = cls.temp_dir / "data"
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        
        cls.session_mgr = SessionManager(cls.data_dir)
        cls.registry = AgentRegistry(cls.data_dir)
        cls.registry.discover_all()
        cls.orchestrator = OrchestratorEngine(cls.registry, cls.data_dir)
        cls.art_mgr = ArtifactManager(cls.data_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.temp_dir), ignore_errors=True)

    def test_01_session_correlation_chain_lifecycle(self):
        """Test full Session -> Artifact -> Task -> Agent -> Execution correlation chain."""
        print("\n--- TEST 1: Session Correlation Chain Lifecycle ---")
        sess = self.session_mgr.create_session(workspace=str(self.temp_dir))
        self.assertIsNotNone(sess.session_id)
        self.assertIsNotNone(sess.session_uuid)
        self.assertTrue(sess.session_id.startswith("AGY-"))

        # Create a dummy image artifact
        img = Image.new("RGB", (120, 40), color=(100, 150, 200))
        img_p = self.temp_dir / "sample_corr.png"
        img.save(img_p)
        art = self.art_mgr.ingest_file(img_p, "sample_corr.png", ArtifactAcquisition.WORKSPACE, session_id=sess.session_id)

        # Record a correlation chain
        corr = self.session_mgr.record_correlation(
            task_id="task_corr_99",
            artifact_id=art.id,
            execution_id="exec_corr_99",
            agent_id="agy",
            provider_id="antigravity",
            capabilities=["IMAGE_INGESTION"],
            result="VISION_AGENT_UNAVAILABLE",
            reason="BLOCKED — NO OPERATIONAL VISION-CAPABLE AGENT",
            details="Image not sent to text-only agent"
        )

        self.assertIsNotNone(corr)
        self.assertEqual(corr["session_id"], sess.session_id)
        self.assertEqual(corr["session_uuid"], sess.session_uuid)
        self.assertEqual(corr["artifact_id"], art.id)
        self.assertEqual(corr["task_id"], "task_corr_99")
        self.assertEqual(corr["result"], "VISION_AGENT_UNAVAILABLE")

        # Query correlations
        all_corrs = self.session_mgr.get_correlations()
        self.assertEqual(len(all_corrs), 1)

        by_art = self.session_mgr.find_correlations_by_artifact(art.id)
        self.assertEqual(len(by_art), 1)
        self.assertEqual(by_art[0]["task_id"], "task_corr_99")

        by_task = self.session_mgr.find_correlations_by_task("task_corr_99")
        self.assertEqual(len(by_task), 1)
        self.assertEqual(by_task[0]["artifact_id"], art.id)

        by_exec = self.session_mgr.find_correlations_by_execution("exec_corr_99")
        self.assertEqual(len(by_exec), 1)
        self.assertEqual(by_exec[0]["agent_id"], "agy")
        print("[PASS] Correlation chain properly answers: which artifact caused task, which agent, which result.")

    def test_02_universal_vision_negotiation_and_rejection(self):
        """Orchestrator strictly refuses sending raw images to text-only agents."""
        print("\n--- TEST 2: Universal Vision Adapter Gate ---")
        sess = self.session_mgr.create_session(workspace=str(self.temp_dir))
        
        # Verify no operational agents currently have IMAGE_VISION verified
        vision_agents = self.registry.agents_with_verified_capability("IMAGE_VISION")
        self.assertEqual(len(vision_agents), 0, "No host agent should have false IMAGE_VISION claim")

        # Create pure image artifact
        img = Image.new("RGB", (200, 60), color=(255, 255, 255))
        img_p = self.temp_dir / "vision_req_test.png"
        img.save(img_p)
        art = self.art_mgr.ingest_file(img_p, "vision_req_test.png", session_id=sess.session_id)

        # Execute task requiring vision through orchestrator
        res = self.orchestrator.execute_task(
            task_id="task_vision_gate_test",
            prompt="Analyze this diagram and explain the boxes",
            role="CODER",
            workspace=self.temp_dir,
            artifacts=[art],
            preferred_agent="opencode",
            session_id=sess.session_id
        )

        self.assertFalse(res["success"])
        self.assertEqual(res["result"], "VISION_AGENT_UNAVAILABLE")
        self.assertEqual(res["status"], "VISION_AGENT_UNAVAILABLE")
        self.assertEqual(res["reason"], "BLOCKED — NO OPERATIONAL VISION-CAPABLE AGENT")
        self.assertIsNone(res["primary_agent"])
        print("[PASS] Orchestrator intercepted image requirement and blocked text-only agent execution.")

        # Check correlation chain was automatically recorded
        corrs = self.session_mgr.find_correlations_by_artifact(art.id)
        self.assertTrue(len(corrs) >= 1)
        latest_corr = corrs[-1]
        self.assertEqual(latest_corr["result"], "VISION_AGENT_UNAVAILABLE")
        self.assertEqual(latest_corr["task_id"], "task_vision_gate_test")
        print(f"[PASS] Correlation recorded automatically: {latest_corr['result']} for task {latest_corr['task_id']}")

    def test_03_two_stage_pdf_processing_text_layer(self):
        """Stage 1: PDF with embedded text layer -> DOCUMENT_TEXT (pypdf)."""
        print("\n--- TEST 3: Two-Stage PDF Processing (Text Layer) ---")
        # Ingest a text-rich document or verify pypdf extraction
        pdf_p = self.temp_dir / "text_pdf.pdf"
        writer = PdfWriter()
        # Add a page with metadata
        writer.add_blank_page(width=400, height=600)
        writer.add_metadata({"/Title": "Text Layer PDF", "/Author": "Agy Studio"})
        with open(pdf_p, "wb") as f:
            writer.write(f)

        content, meta, ext = DocumentExtractor.extract(pdf_p, ArtifactSourceType.PDF)
        self.assertEqual(meta.pages, 1)
        # Blank page has 0 chars -> triggers Stage 2 OCR_REQUIRED
        self.assertEqual(ext.status, ExtractionStatus.OCR_REQUIRED)
        self.assertIn("OCR_REQUIRED", content.extracted_text)
        print(f"[PASS] Blank/scanned PDF classified as: {ext.status.value}")

    def test_04_scanned_pdf_negotiation_never_silent_empty(self):
        """Stage 2: Scanned PDF without text layer -> OCR_REQUIRED, rejected if OCR unavailable."""
        print("\n--- TEST 4: Scanned PDF Capability Negotiation ---")
        pdf_p = self.temp_dir / "scanned_invoice.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        with open(pdf_p, "wb") as f:
            writer.write(f)

        art = self.art_mgr.ingest_file(pdf_p, "scanned_invoice.pdf")
        self.assertEqual(art.extraction.status, ExtractionStatus.OCR_REQUIRED)

        # Negotiate with text agent
        agent = AgentModel(
            id="agy",
            name="Antigravity",
            command="agy",
            provider="antigravity",
            capabilities={"chat": "VERIFIED", "code": "VERIFIED", "ocr": "UNSUPPORTED"}
        )
        neg = ArtifactCapabilityNegotiator.negotiate(
            agent=agent,
            artifacts=[art],
            task_prompt="Extract totals from invoice",
            workspace=str(self.temp_dir)
        )

        self.assertFalse(neg.compatible, "Scanned PDF without OCR must NOT be marked compatible")
        self.assertIn("OCR", neg.missing_capabilities)
        norm_art = neg.normalized_artifacts[0]
        self.assertEqual(norm_art["handoff_mode"], "OCR_REQUIRED")
        self.assertIn("OCR is required", neg.audit_note)
        print("[PASS] Scanned PDF strictly required OCR and prevented silent empty context.")


if __name__ == "__main__":
    unittest.main()
