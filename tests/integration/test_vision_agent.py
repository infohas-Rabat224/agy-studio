"""
Vision Agent Verification Probe for Agy Studio.
Tests deterministic image generation, ingestion, SHA-256 calculation,
and strict multi-stage vision capability negotiation:
1. IMAGE_INGESTION_VERIFIED: Image received, persisted, dimensions & SHA-256 calculated.
2. IMAGE_AGENT_DELIVERY_VERIFIED: Vision-capable operational agent receives native image.
3. IMAGE_UNDERSTANDING_VERIFIED: Vision-capable agent reads exact text from image.

Strictly enforces:
- Never send raw images to text-only agents.
- Never infer IMAGE_VISION from IMAGE_INGESTION.
- Never infer OCR from IMAGE_VISION.
- When no operational vision agent is available, return VISION_AGENT_UNAVAILABLE honestly.
"""

import os
import sys
import time
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.agent_adapters import (
    AgentRegistry, OrchestratorEngine, AgentStatus, CapabilityStatus
)
from backend.artifacts.artifact_manager import ArtifactManager
from backend.artifacts.capability_negotiator import ArtifactCapabilityNegotiator
from backend.artifacts.models import ArtifactAcquisition, ArtifactSourceType

DETERMINISTIC_TEXT = "AGY VISION TEST 847291"
TEST_IMG_WIDTH = 320
TEST_IMG_HEIGHT = 80


def generate_deterministic_test_image(output_path: Path, text: str = DETERMINISTIC_TEXT) -> Path:
    """
    Generates a deterministic 320x80 PNG image with distinct high-contrast text.
    """
    img = Image.new("RGB", (TEST_IMG_WIDTH, TEST_IMG_HEIGHT), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw simple frame border
    draw.rectangle([(2, 2), (TEST_IMG_WIDTH - 3, TEST_IMG_HEIGHT - 3)], outline=(0, 51, 102), width=2)
    
    # Draw deterministic text using standard bitmap font
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # Center-ish positioning
    draw.text((25, 32), text, fill=(0, 0, 0), font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), format="PNG")
    return output_path


def execute_vision_probe(
    data_dir: Optional[Path] = None,
    output_evidence_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Executes the full vision verification probe.
    Returns forensic probe result dictionary.
    """
    data_dir = data_dir or (ROOT_DIR / "data")
    evidence_path = output_evidence_file or (data_dir / "forensic_vision_probe.json")
    
    temp_dir = Path(tempfile.mkdtemp(prefix="agy_vision_probe_"))
    try:
        # Step 1 & 2: Generate deterministic test image
        img_file = temp_dir / "deterministic_vision_test.png"
        generate_deterministic_test_image(img_file, DETERMINISTIC_TEXT)
        
        # Step 3: Register as an artifact
        art_mgr = ArtifactManager(data_dir=data_dir)
        artifact = art_mgr.ingest_file(
            source=img_file,
            filename="deterministic_vision_test.png",
            acquisition=ArtifactAcquisition.WORKSPACE
        )
        
        # Validate ingestion
        image_ingestion_verified = bool(
            artifact and
            artifact.sha256 and
            artifact.metadata.width == TEST_IMG_WIDTH and
            artifact.metadata.height == TEST_IMG_HEIGHT and
            artifact.mime_type == "image/png"
        )
        
        # Step 4: Discover operational agents and inspect verified capability matrix
        registry = AgentRegistry(data_dir=data_dir)
        registry.discover_all()
        
        vision_candidates: List[Dict[str, Any]] = []
        text_only_agents: List[str] = []
        
        for agent in registry.list_agents():
            aid = agent["id"]
            caps = agent.get("capabilities", {})
            vision_status = str(
                caps.get("IMAGE_VISION") or
                caps.get("image_vision") or
                caps.get("vision") or ""
            ).upper()
            
            # Step 5: Do NOT send the image to a text-only agent
            if vision_status == CapabilityStatus.VERIFIED.value:
                # Also check if agent is OPERATIONAL
                if agent["status"] == AgentStatus.OPERATIONAL.value:
                    vision_candidates.append(agent)
                else:
                    # Try to verify
                    ver = registry.verify_agent(aid)
                    if ver.get("status") == AgentStatus.OPERATIONAL.value:
                        vision_candidates.append(registry.get_agent(aid))
            else:
                text_only_agents.append(aid)

        forensic_record: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "probe_type": "DETERMINISTIC_VISION_PROBE",
            "test_target_text": DETERMINISTIC_TEXT,
            "artifact_id": artifact.id,
            "artifact_sha256": artifact.sha256,
            "artifact_dimensions": f"{artifact.metadata.width}x{artifact.metadata.height}",
            "artifact_mime_type": artifact.mime_type,
            "image_ingestion_verified": image_ingestion_verified,
            "image_agent_delivery_verified": False,
            "image_understanding_verified": False,
            "text_only_agents_suppressed": sorted(text_only_agents),
            "vision_candidates_found": [c["id"] for c in vision_candidates]
        }

        # Step 6: Check availability of real vision-capable operational CLI
        if not vision_candidates:
            forensic_record["status"] = "VISION_AGENT_UNAVAILABLE"
            forensic_record["reason"] = "BLOCKED — NO OPERATIONAL VISION-CAPABLE AGENT"
            forensic_record["details"] = (
                f"Host contains {len(text_only_agents)} registered CLI agents ({', '.join(text_only_agents)}), "
                "none of which have verified IMAGE_VISION capability. "
                "Per anti-fabrication rules, raw images are not delivered to text-only agents."
            )
            
            # Persist forensic evidence
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            with open(evidence_path, "w", encoding="utf-8") as f:
                json.dump(forensic_record, f, indent=2)
            
            return forensic_record

        # Step 7 & 8: If vision candidate exists, deliver image and query
        selected = vision_candidates[0]
        selected_id = selected["id"]
        orchestrator = OrchestratorEngine(registry, data_dir=data_dir)
        
        prompt = "Read the exact text visible in the supplied image. Respond with only the text."
        start_time = time.time()
        
        exec_res = orchestrator.execute_task(
            task_id=f"vision_probe_{int(time.time())}",
            prompt=prompt,
            role="CODER",
            workspace=temp_dir,
            preferred_agent=selected_id,
            artifacts=[artifact],
            allow_fallback=False
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Step 9: Capture all forensic fields
        forensic_record["image_agent_delivery_verified"] = True
        forensic_record["execution_details"] = {
            "agent_id": selected_id,
            "command": exec_res.get("command_redacted"),
            "pid": exec_res.get("pid"),
            "provider": exec_res.get("provider_id"),
            "model": exec_res.get("model"),
            "exit_code": exec_res.get("exit_code"),
            "duration_ms": duration_ms,
            "stdout": exec_res.get("stdout"),
            "stderr": exec_res.get("stderr")
        }

        # Step 10: Verify stdout contains DETERMINISTIC_TEXT
        stdout_txt = exec_res.get("stdout", "")
        if DETERMINISTIC_TEXT in stdout_txt:
            forensic_record["status"] = "SUCCESS"
            forensic_record["image_understanding_verified"] = True
        else:
            forensic_record["status"] = "FAILED"
            forensic_record["image_understanding_verified"] = False
            forensic_record["reason"] = f"Agent output did not contain exact expected text '{DETERMINISTIC_TEXT}'"

        # Step 11: Persist forensic evidence
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(forensic_record, f, indent=2)

        return forensic_record

    finally:
        shutil.rmtree(str(temp_dir), ignore_errors=True)


class VisionAgentIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="agy_vision_test_"))
        cls.data_dir = cls.temp_dir / "data"
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        cls.evidence_file = cls.data_dir / "forensic_vision_probe.json"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.temp_dir), ignore_errors=True)

    def test_01_deterministic_image_generation_and_ingestion(self):
        """Verify deterministic image creation, dimensions, SHA-256, and ingestion."""
        print("\n--- VISION TEST 1: Deterministic Image Ingestion ---")
        img_path = self.temp_dir / "test_det.png"
        generate_deterministic_test_image(img_path, DETERMINISTIC_TEXT)
        self.assertTrue(img_path.exists())
        
        art_mgr = ArtifactManager(data_dir=self.data_dir)
        art = art_mgr.ingest_file(img_path, "test_det.png", ArtifactAcquisition.WORKSPACE)
        
        self.assertIsNotNone(art)
        self.assertEqual(art.metadata.width, TEST_IMG_WIDTH)
        self.assertEqual(art.metadata.height, TEST_IMG_HEIGHT)
        self.assertEqual(art.mime_type, "image/png")
        self.assertIsNotNone(art.sha256)
        self.assertEqual(len(art.sha256), 64)
        print(f"[PASS] Image ingested: {art.id}, SHA-256={art.sha256[:16]}..., dims={art.metadata.width}x{art.metadata.height}")

    def test_02_strict_vision_probe_execution(self):
        """Execute vision probe: verify truth-in-reporting and absence of false multimodal claims."""
        print("\n--- VISION TEST 2: Vision Probe Execution ---")
        res = execute_vision_probe(data_dir=self.data_dir, output_evidence_file=self.evidence_file)
        
        self.assertTrue(res["image_ingestion_verified"])
        self.assertTrue(self.evidence_file.exists())
        
        if res["status"] == "VISION_AGENT_UNAVAILABLE":
            print(f"[EXPECTED RESULT] Vision probe honestly reported: {res['status']}")
            print(f"Reason: {res['reason']}")
            print(f"Suppressed text-only agents: {res['text_only_agents_suppressed']}")
            self.assertFalse(res["image_agent_delivery_verified"])
            self.assertFalse(res["image_understanding_verified"])
            self.assertEqual(res["reason"], "BLOCKED — NO OPERATIONAL VISION-CAPABLE AGENT")
        else:
            self.assertEqual(res["status"], "SUCCESS")
            self.assertTrue(res["image_agent_delivery_verified"])
            self.assertTrue(res["image_understanding_verified"])
            print(f"[PASS] Vision understanding verified with agent {res['execution_details']['agent_id']}")

    def test_03_never_infer_vision_from_ingestion_or_ocr(self):
        """Verify that capability negotiator strictly separates INGESTION, DELIVERY, and UNDERSTANDING."""
        print("\n--- VISION TEST 3: Capability Model Strictness ---")
        img_path = self.temp_dir / "test_cap.png"
        generate_deterministic_test_image(img_path, DETERMINISTIC_TEXT)
        
        art_mgr = ArtifactManager(data_dir=self.data_dir)
        art = art_mgr.ingest_file(img_path, "test_cap.png", ArtifactAcquisition.WORKSPACE)
        
        registry = AgentRegistry(data_dir=self.data_dir)
        opencode_dict = registry.get_agent("opencode")
        
        if opencode_dict:
            from backend.agent_adapters.base import AgentModel
            opencode = AgentModel(**opencode_dict)
            # OpenCode is text-only. Negotiating with OpenCode must NOT mark image delivery as native
            neg = ArtifactCapabilityNegotiator.negotiate(
                agent=opencode,
                artifacts=[art],
                task_prompt="What is in this image?",
                workspace=str(self.temp_dir)
            )
            self.assertTrue(neg.image_ingestion_verified, "Ingestion must be verified")
            self.assertFalse(neg.image_agent_delivery_verified, "Delivery to text-only agent must NOT be verified")
            self.assertFalse(neg.image_understanding_verified, "Understanding must NOT be verified")
            print(f"[PASS] Negotiator strictly refused vision delivery for text-only agent 'opencode'")


if __name__ == "__main__":
    unittest.main()
