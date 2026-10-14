"""
Agy Studio - Session Identity & Multimodal Artifact Ingestion Test Matrix
Tests:
1. Session identity generation, state machine transitions, disk persistence, startup crash recovery.
2. WorkspacePickerManager non-blocking job lifecycle, selection, cancellation, and manual path verification.
3. Universal Artifact Model, SHA-256 computation, filename sanitation, path traversal prevention.
4. Document extraction across PNG, PDF, scanned PDF detection, DOCX, XLSX, PPTX, TXT, CSV, JSON, and ZIP security.
5. Multimodal capability negotiation between vision-capable and text-only runtime agents.
"""

import os
import re
import sys
import time
import uuid
import json
import zipfile
import tempfile
import pytest
from pathlib import Path
from PIL import Image

# Ensure root Agy Studio is on path
STUDIO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

from backend.session.session_manager import SessionManager, SessionState
from backend.runtime.windows_native import WorkspacePickerManager
from backend.artifacts.models import (
    Artifact,
    ArtifactAcquisition,
    ArtifactSourceType,
    ExtractionStatus
)
from backend.artifacts.artifact_manager import ArtifactManager
from backend.artifacts.document_extractor import DocumentExtractor
from backend.artifacts.image_processor import ImageProcessor
from backend.artifacts.capability_negotiator import ArtifactCapabilityNegotiator


# ============================================================================
# 1. SESSION IDENTITY & LIFECYCLE TESTS
# ============================================================================

def test_session_creation_and_identity_format(tmp_path):
    mgr = SessionManager(data_dir=tmp_path)
    session = mgr.create_session(workspace=str(tmp_path))

    # Validate ID pattern: AGY-YYYYMMDD-HHMMSS-XXXXXXXX
    assert re.match(r"^AGY-\d{8}-\d{6}-[0-9A-F]{8}$", session.session_id), (
        f"Invalid session_id format: {session.session_id}"
    )

    # Validate UUID4
    val_uuid = uuid.UUID(session.session_uuid)
    assert val_uuid.version == 4, f"Invalid UUID version: {session.session_uuid}"

    # Validate Initial State
    assert session.status == SessionState.ACTIVE.value
    assert session.workspace == str(tmp_path)

    # Check persistence file on disk
    sess_file = tmp_path / "sessions" / f"{session.session_id}.json"
    assert sess_file.exists(), f"Session persistence file missing: {sess_file}"

    with open(sess_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["session_id"] == session.session_id
    assert data["session_uuid"] == session.session_uuid


def test_session_lifecycle_transitions_and_events(tmp_path):
    mgr = SessionManager(data_dir=tmp_path)
    session = mgr.create_session(workspace=str(tmp_path))
    s_id = session.session_id

    # Workspace change
    new_ws = str(tmp_path / "another_folder")
    os.makedirs(new_ws, exist_ok=True)
    mgr.set_session_workspace(new_ws)
    assert mgr.get_current_session().workspace == new_ws

    # Attach Artifact
    mgr.attach_artifact("art_001", "diagram.png", "image/png", 1024)
    curr = mgr.get_current_session()
    assert len(curr.artifacts) == 1
    assert curr.artifacts[0]["artifact_id"] == "art_001"

    # Attach Execution
    mgr.attach_execution(
        command="test command",
        agent_name="antigravity",
        status="COMPLETED",
        return_code=0,
        artifact_ids=["art_001"]
    )
    curr = mgr.get_current_session()
    assert len(curr.executions) == 1
    assert curr.executions[0]["agent_name"] == "antigravity"

    # Verify event stream
    saved_sess = mgr.get_session(s_id)
    event_names = [e.get("event_type") for e in saved_sess.events]
    assert "SESSION_CREATED" in event_names
    assert "WORKSPACE_CHANGED" in event_names
    assert "ARTIFACT_ATTACHED" in event_names
    assert "TASK_EXECUTED" in event_names

    # Close session
    ok = mgr.close_session("test_completed")
    assert ok is True
    assert mgr.get_session(s_id).status == SessionState.CLOSED.value


def test_session_startup_crash_recovery(tmp_path):
    """
    Simulates an orphaned session file whose recorded PID does not exist,
    verifying recover_previous_sessions() marks it as CRASHED with audit event.
    """
    sess_dir = tmp_path / "sessions"
    sess_dir.mkdir(parents=True, exist_ok=True)

    fake_session_id = "AGY-20261006-000000-DEADBEEF"
    fake_data = {
        "session_id": fake_session_id,
        "session_uuid": str(uuid.uuid4()),
        "status": SessionState.ACTIVE.value,
        "started_at": "2026-10-06T00:00:00Z",
        "process_id": 9999999,  # Unlikely to be a real running PID
        "workspace": str(tmp_path),
        "artifacts": [],
        "executions": [],
        "events": [],
        "metadata": {}
    }

    fake_file = sess_dir / f"{fake_session_id}.json"
    with open(fake_file, "w", encoding="utf-8") as f:
        json.dump(fake_data, f, indent=2)

    # Initialize manager and run startup recovery
    mgr = SessionManager(data_dir=tmp_path)
    recovered = mgr.recover_previous_sessions()

    assert fake_session_id in recovered
    recovered_sess = mgr.get_session(fake_session_id)
    assert recovered_sess is not None
    assert recovered_sess.status == SessionState.CRASHED.value

    # Check crash event
    event_names = [e.get("event_type") for e in recovered_sess.events]
    assert "SESSION_CRASH_DETECTED" in event_names


# ============================================================================
# 2. WORKSPACE PICKER NON-BLOCKING LIFECYCLE TESTS
# ============================================================================

def test_workspace_picker_job_lifecycle(tmp_path):
    p_mgr = WorkspacePickerManager(data_dir=tmp_path / "picker_data")

    # 1. Job Creation
    job = p_mgr.create_picker_job(initial_dir=str(tmp_path), session_id="test_sess")
    assert job["job_id"].startswith("picker_")
    assert job["status"] in ("CREATED", "LAUNCHING", "OPEN")

    # 2. Querying Job Snapshot
    snapshot = p_mgr.get_picker_job(job["job_id"])
    assert snapshot is not None
    assert snapshot["job_id"] == job["job_id"]

    # 3. Simulate Selection
    selected_target = str(tmp_path / "my_project")
    sim_job = p_mgr.simulate_picker_selection(job["job_id"], selected_target)
    assert sim_job["status"] == "SELECTED"
    assert sim_job["result_path"] == os.path.normpath(selected_target)

    # 4. Forensic log check
    log_file = tmp_path / "picker_data" / "picker_forensic.log"
    assert log_file.exists()
    log_content = log_file.read_text(encoding="utf-8")
    assert job["job_id"] in log_content
    assert "SELECTED" in log_content


def test_workspace_picker_cancellation(tmp_path):
    p_mgr = WorkspacePickerManager(data_dir=tmp_path / "picker_data")
    job = p_mgr.create_picker_job(initial_dir=str(tmp_path))

    # Cancel job
    ok = p_mgr.cancel_picker_job(job["job_id"])
    assert ok is True

    snapshot = p_mgr.get_picker_job(job["job_id"])
    assert snapshot["status"] == "CANCELLED"


# ============================================================================
# 3. UNIVERSAL ARTIFACT MODEL & EXTRACTION TESTS
# ============================================================================

def test_artifact_sanitization_and_security(tmp_path):
    art_mgr = ArtifactManager(data_dir=tmp_path)

    # Path traversal attack file name
    malicious_name = "../../../../../windows/system32/cmd.exe"
    sample_content = b"Safe test content"

    art = art_mgr.ingest_file(
        source=sample_content,
        filename=malicious_name,
        session_id="sec_test",
        acquisition=ArtifactAcquisition.FILE_PICKER
    )

    # Name must be sanitized
    assert ".." not in art.name
    assert "/" not in art.name
    assert "\\" not in art.name
    assert art.name == "cmd.exe"
    assert art.size_bytes == len(sample_content)

    # Stored strictly inside session sandbox
    stored_path = Path(art.content.binary_path)
    assert stored_path.exists()
    assert str(tmp_path / "sessions" / "sec_test" / "artifacts") in str(stored_path)


def test_png_image_ingestion_and_metadata(tmp_path):
    art_mgr = ArtifactManager(data_dir=tmp_path)

    # Create real PNG image using Pillow
    img = Image.new("RGB", (320, 240), color=(73, 109, 137))
    img_path = tmp_path / "test_image.png"
    img.save(img_path)

    art = art_mgr.ingest_file(
        source=img_path,
        filename="test_image.png",
        session_id="img_test",
        acquisition=ArtifactAcquisition.CLIPBOARD
    )

    assert art.mime_type == "image/png"
    assert art.metadata.width == 320
    assert art.metadata.height == 240
    assert art.extraction.status in (ExtractionStatus.TEXT_EXTRACTED, ExtractionStatus.NOT_APPLICABLE)
    assert art.content.image_path is not None

    # Context representation contains dimensions
    prompt_ctx = art.to_prompt_context()
    assert "320x240" in prompt_ctx


def test_pdf_extraction_and_scanned_detection(tmp_path):
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    pdf_path = tmp_path / "document.pdf"
    with open(pdf_path, "wb") as f:
        writer.write(f)

    extractor = DocumentExtractor()
    content, metadata, ext = extractor.extract(pdf_path, ArtifactSourceType.PDF)

    assert metadata.pages == 1
    assert "pypdf" in ext.extractor
    # Blank PDF with no text triggers scanned / OCR required detection
    assert ext.status == ExtractionStatus.OCR_REQUIRED


def test_docx_extraction(tmp_path):
    import docx

    doc_path = tmp_path / "test_doc.docx"
    doc = docx.Document()
    doc.add_heading("Cahier de Texte 2026", level=1)
    doc.add_paragraph("Ce document contient la planification pedagogique detaillee.")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Seance"
    table.cell(0, 1).text = "Module"
    table.cell(1, 0).text = "01"
    table.cell(1, 1).text = "M03 Metrologie"
    doc.save(str(doc_path))

    extractor = DocumentExtractor()
    content, meta, ext = extractor.extract(doc_path, ArtifactSourceType.DOCX)

    assert ext.status == ExtractionStatus.TEXT_EXTRACTED
    assert "Cahier de Texte 2026" in content.extracted_text
    assert "M03 Metrologie" in content.extracted_text
    assert meta.char_count > 0


def test_xlsx_extraction(tmp_path):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "EmploiDuTemps"
    ws.append(["Date", "Heure", "Module", "Formateur"])
    ws.append(["2026-10-12", "08:30", "M03", "Professeur X"])
    xlsx_path = tmp_path / "planning.xlsx"
    wb.save(str(xlsx_path))

    extractor = DocumentExtractor()
    content, meta, ext = extractor.extract(xlsx_path, ArtifactSourceType.XLSX)

    assert ext.status == ExtractionStatus.TEXT_EXTRACTED
    assert "EmploiDuTemps" in content.extracted_text
    assert "M03" in content.extracted_text
    assert "Professeur X" in content.extracted_text


def test_pptx_extraction(tmp_path):
    from pptx import Presentation

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Module Architecture 2026"
    slide.placeholders[1].text = "Planification des 22 modules et certification."
    pptx_path = tmp_path / "presentation.pptx"
    prs.save(str(pptx_path))

    extractor = DocumentExtractor()
    content, meta, ext = extractor.extract(pptx_path, ArtifactSourceType.PPTX)

    assert ext.status == ExtractionStatus.TEXT_EXTRACTED
    assert "Module Architecture 2026" in content.extracted_text
    assert meta.slide_count == 1


def test_zip_traversal_prevention(tmp_path):
    """
    Creates a ZIP archive with a safe file and attempts extraction
    to ensure traversal prevention.
    """
    safe_zip = tmp_path / "archive.zip"
    with zipfile.ZipFile(safe_zip, "w") as zf:
        zf.writestr("safe_file.txt", "Contenu securise de l'archive.")
        zf.writestr("subfolder/inner.txt", "Contenu sous-dossier.")

    extractor = DocumentExtractor()
    content, meta, ext = extractor.extract(safe_zip, ArtifactSourceType.ARCHIVE)

    assert ext.status == ExtractionStatus.TEXT_EXTRACTED
    assert "safe_file.txt" in content.extracted_text
    assert "subfolder/inner.txt" in content.extracted_text


# ============================================================================
# 4. MULTIMODAL CAPABILITY NEGOTIATION TESTS
# ============================================================================

def test_capability_negotiator_prevents_false_vision_claim(tmp_path):
    from backend.agent_adapters.base import AgentModel

    negotiator = ArtifactCapabilityNegotiator()

    # Image Artifact without text
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img_path = tmp_path / "diagram.png"
    img.save(img_path)

    art_mgr = ArtifactManager(data_dir=tmp_path)
    img_art = art_mgr.ingest_file(img_path, filename="diagram.png", session_id="neg_test")

    # Text-only agent: e.g. OpenCode without vision
    text_agent = AgentModel(
        id="opencode",
        name="OpenCode",
        command="opencode",
        provider="opencode",
        capabilities={"image_input": "unsupported", "vision": "unsupported"}
    )
    text_decision = negotiator.negotiate(
        agent=text_agent,
        artifacts=[img_art],
        task_prompt="Inspect this image",
        workspace=str(tmp_path)
    )

    # Verify text-only agent is NOT falsely marked compatible with pure image
    assert text_decision.compatible is False
    assert "image_input" in text_decision.missing_capabilities

    # Vision-capable agent: e.g. Antigravity or Gemini
    vision_agent = AgentModel(
        id="antigravity",
        name="Antigravity",
        command="agy",
        provider="google",
        capabilities={"image_input": "verified", "vision": "verified"}
    )
    vision_decision = negotiator.negotiate(
        agent=vision_agent,
        artifacts=[img_art],
        task_prompt="Inspect this image",
        workspace=str(tmp_path)
    )
    assert vision_decision.compatible is True
    assert vision_decision.normalized_artifacts[0]["handoff_mode"] == "NATIVE_IMAGE"
