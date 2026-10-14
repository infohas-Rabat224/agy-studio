"""
Agy Studio — Production Test Suite: Persistent Sessions & Learning Memory System
Verifies:
1. Session Pinning, Unpinning, Renaming, Archiving, Restoring, Soft & Permanent Deletion.
2. Non-destructive Session Resume (creates new runtime session with lineage link).
3. Session Forking and Lineage Graph.
4. Cross-Session Learning (Session A correction retrieved in Session B).
5. Anti-Repetition Guard & Previously Rejected Implementation Regression Test.
6. Application Restart Memory Persistence.
"""

import os
import sys
import shutil
import tempfile
import pytest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.session.session_manager import SessionManager, SessionState
from backend.memory.memory_manager import MemoryManager
from backend.memory.memory_models import (
    MemoryRecord, MemoryScope, MemoryType,
    MemoryPriority, MemoryConfidence, MemoryCreateRequest
)

@pytest.fixture
def test_env():
    temp_dir = Path(tempfile.mkdtemp(prefix="agy_test_data_"))
    session_mgr = SessionManager(temp_dir)
    memory_mgr = MemoryManager(temp_dir)
    yield {
        "data_dir": temp_dir,
        "session_mgr": session_mgr,
        "memory_mgr": memory_mgr
    }
    shutil.rmtree(temp_dir, ignore_errors=True)

# ----------------- SESSION LIFECYCLE TESTS -----------------

def test_session_creation_and_naming(test_env):
    sm: SessionManager = test_env["session_mgr"]
    sess = sm.create_session(workspace="C:/Projects/QatarRecruit", display_name="Qatar Recruitment Platform")
    assert sess.session_id.startswith("AGY-")
    assert sess.display_name == "Qatar Recruitment Platform"
    assert sess.pinned is False
    assert sess.archived is False
    assert sess.deleted is False
    assert sess.status == SessionState.ACTIVE.value

    # Auto-derivation test on task prompt
    sess2 = sm.create_session(workspace="C:/Projects/ATS")
    sm.attach_task(task_id="t1", prompt="Implement DOCX resume layout optimizer for aviation candidates")
    assert sess2.display_name == "DOCX resume layout optimizer for aviation candidates"

def test_session_pin_unpin_archive_restore(test_env):
    sm: SessionManager = test_env["session_mgr"]
    sess = sm.create_session(display_name="Critical Server Deployment")
    sid = sess.session_id

    # Pin
    assert sm.pin_session(sid) is True
    reloaded = sm.get_session(sid)
    assert reloaded.pinned is True

    # Pinned appears first in list
    sess_unpinned = sm.create_session(display_name="Unpinned Scratchpad")
    sessions = sm.list_sessions()
    assert sessions[0]["session_id"] == sid
    assert sessions[0]["pinned"] is True

    # Unpin
    assert sm.unpin_session(sid) is True
    assert sm.get_session(sid).pinned is False

    # Archive & Restore
    assert sm.archive_session(sid) is True
    assert sm.get_session(sid).archived is True
    assert sm.restore_session(sid) is True
    assert sm.get_session(sid).archived is False

def test_session_rename(test_env):
    sm: SessionManager = test_env["session_mgr"]
    sess = sm.create_session(display_name="Old Title")
    sid = sess.session_id
    suuid = sess.session_uuid

    assert sm.rename_session(sid, "INFOHAS ATS — Resume Optimization") is True
    updated = sm.get_session(sid)
    assert updated.display_name == "INFOHAS ATS — Resume Optimization"
    # Immutable identities MUST NOT change
    assert updated.session_id == sid
    assert updated.session_uuid == suuid
    # Verify event recorded
    renamed_events = [e for e in updated.events if e.get("event_type") == "SESSION_RENAMED"]
    assert len(renamed_events) == 1
    assert renamed_events[0]["payload"]["new_name"] == "INFOHAS ATS — Resume Optimization"

def test_session_soft_and_permanent_delete(test_env):
    sm: SessionManager = test_env["session_mgr"]
    sess = sm.create_session(display_name="Session to Delete")
    sid = sess.session_id

    # 1. Soft delete
    assert sm.delete_session(sid) is True
    assert sm.get_session(sid).deleted is True
    assert sid not in [s["session_id"] for s in sm.list_sessions(include_deleted=False)]
    assert sid in [s["session_id"] for s in sm.list_sessions(include_deleted=True)]

    # Restore from trash
    assert sm.restore_session(sid) is True
    assert sm.get_session(sid).deleted is False

    # 2. Permanent deletion guard: Pinned session CANNOT be deleted
    sm.pin_session(sid)
    ok, msg = sm.delete_permanently(sid)
    assert ok is False
    assert "Pinned sessions cannot be deleted" in msg

    # Unpin and delete permanently
    sm.unpin_session(sid)
    ok, msg = sm.delete_permanently(sid)
    assert ok is True
    assert sm.get_session(sid) is None

def test_session_resume_preserves_forensic_integrity(test_env):
    sm: SessionManager = test_env["session_mgr"]
    sess_old = sm.create_session(workspace="C:/Agy Studio", display_name="Infra Setup")
    old_id = sess_old.session_id
    sm.attach_task("t1", "Prepare server configuration")
    sm.close_session("Completed phase 1")
    assert sm.get_session(old_id).status == SessionState.CLOSED.value

    # Resume: MUST NOT overwrite old session, must create new session
    resumed_sess = sm.resume_session(old_id)
    assert resumed_sess.session_id != old_id
    assert resumed_sess.parent_session_id == old_id
    assert resumed_sess.resume_source_session_id == old_id
    assert resumed_sess.workspace == "C:/Agy Studio"
    assert resumed_sess.status == SessionState.ACTIVE.value
    # Old session is still preserved intact
    assert sm.get_session(old_id).status == SessionState.CLOSED.value

    # Check lineage
    lineage = sm.get_session_lineage(resumed_sess.session_id)
    assert len(lineage["ancestors"]) == 1
    assert lineage["ancestors"][0]["session_id"] == old_id

def test_session_fork(test_env):
    sm: SessionManager = test_env["session_mgr"]
    sess_orig = sm.create_session(display_name="INFOHAS ATS — Production")
    orig_id = sess_orig.session_id

    forked = sm.fork_session(orig_id, fork_name="INFOHAS ATS — Experimental OCR")
    assert forked.session_id != orig_id
    assert forked.parent_session_id == orig_id
    assert forked.display_name == "INFOHAS ATS — Experimental OCR"

    lineage = sm.get_session_lineage(orig_id)
    assert any(c["session_id"] == forked.session_id for c in lineage["children"])

def test_session_search(test_env):
    sm: SessionManager = test_env["session_mgr"]
    sess1 = sm.create_session(display_name="Qatar Recruitment Platform")
    sm.attach_task("t1", "Scrape aviation job requirements from Qatar Airways")

    sess2 = sm.create_session(display_name="AgenticOS Windows Helper")
    sm.attach_task("t2", "Compile AgyStudioFolderPicker.exe native bridge")

    res_qatar = sm.search_sessions("aviation")
    assert len(res_qatar) == 1
    assert res_qatar[0]["session_id"] == sess1.session_id

    res_bridge = sm.search_sessions("bridge")
    assert len(res_bridge) == 1
    assert res_bridge[0]["session_id"] == sess2.session_id

# ----------------- LEARNING MEMORY & REGRESSION TESTS -----------------

def test_cross_session_learning(test_env):
    """
    Mandatory Test Section 36:
    SESSION A: User correction: 'Never claim PASS without real runtime evidence.'
    Session A closed.
    SESSION B created.
    Verify memory preflight in Session B contains the user correction.
    """
    sm: SessionManager = test_env["session_mgr"]
    mm: MemoryManager = test_env["memory_mgr"]

    # 1. SESSION A
    sess_a = sm.create_session(display_name="Session A — Testing Framework")
    # User makes correction
    user_input = "Never claim PASS without real runtime evidence."
    created = mm.learn_from_user(user_input, session_id=sess_a.session_id)
    assert len(created) > 0
    mem_corr = created[0]
    assert mem_corr.confidence == MemoryConfidence.USER_CONFIRMED.value
    assert mem_corr.priority == MemoryPriority.CRITICAL.value
    sm.close_session()

    # 2. SESSION B
    sess_b = sm.create_session(display_name="Session B — Production Audit")
    preflight = mm.preflight_check(
        task="Audit agent verification results and report test status",
        session_id=sess_b.session_id
    )

    assert preflight.has_critical_corrections is True
    assert any("Never claim PASS without real runtime evidence" in c["content"] for c in preflight.corrections)
    assert "Never claim PASS without real runtime evidence" in preflight.context_injection_markdown

def test_previously_rejected_approach_and_anti_repetition_guard(test_env):
    """
    Mandatory Test Section 35:
    Step 1: Task 'Implement workspace picker', agent proposes 'tkinter synchronous picker'.
            User rejects: 'Do not use synchronous tkinter picker because it fails under uv runtime. Use native Windows picker helper instead.'
    Step 2: Store REJECTED_APPROACH, CRITICAL, USER_CONFIRMED.
    Step 3: Start a NEW session B.
    Step 4: Task 'Fix the workspace picker'.
    Step 5: Preflight retrieves REJECTED_APPROACH with reason and accepted alternative.
    Step 6: Anti-Repetition Guard BLOCKS proposal of tkinter synchronous picker.
    Step 7: Proposing native Windows helper is ALLOWED.
    """
    sm: SessionManager = test_env["session_mgr"]
    mm: MemoryManager = test_env["memory_mgr"]

    # Step 1 & 2: User rejection in Session A
    sess_a = sm.create_session(display_name="Session A — Folder Selection")
    user_msg = "Do not use synchronous tkinter picker because it fails under uv runtime. Use native Windows picker helper instead."
    memories = mm.learn_from_user(user_msg, session_id=sess_a.session_id, workspace="C:/Agy Studio")
    assert len(memories) >= 1
    rejected_mem = next(m for m in memories if m.type == MemoryType.REJECTED_APPROACH.value)
    assert "tkinter picker" in rejected_mem.rejected_approach.lower()
    assert "uv runtime" in rejected_mem.reason.lower()
    assert "native windows picker helper" in rejected_mem.accepted_alternative.lower()

    # Close Session A
    sm.close_session()

    # Step 3: Start NEW Session B
    sess_b = sm.create_session(display_name="Session B — Workspace Architecture")

    # Step 4 & 5: Pre-flight check on task
    preflight = mm.preflight_check(
        task="Fix the workspace picker",
        workspace="C:/Agy Studio",
        session_id=sess_b.session_id
    )
    assert preflight.has_rejected_approaches is True
    assert len(preflight.rejected_approaches) >= 1
    assert any("tkinter" in r["rejected_approach"].lower() for r in preflight.rejected_approaches)
    assert "PREVIOUSLY REJECTED APPROACHES" in preflight.context_injection_markdown

    # Step 6: Anti-Repetition Guard blocks reintroducing tkinter
    guard_blocked = mm.check_guard(
        proposal="Let us implement a synchronous tkinter picker for folder selection",
        workspace="C:/Agy Studio",
        session_id=sess_b.session_id
    )
    assert guard_blocked.allowed is False
    assert guard_blocked.violation is True
    assert "PREVIOUSLY REJECTED APPROACH DETECTED" in guard_blocked.warning
    assert "native Windows picker helper" in guard_blocked.accepted_alternative

    # Step 7: Proposal with accepted approach passes cleanly
    guard_ok = mm.check_guard(
        proposal="Spawn AgyStudioFolderPicker.exe native Windows bridge helper",
        workspace="C:/Agy Studio",
        session_id=sess_b.session_id
    )
    assert guard_ok.allowed is True
    assert guard_ok.violation is False

def test_application_restart_memory_persistence(test_env):
    """
    Mandatory Test Section 37:
    1. Create memory.
    2. Close store / simulate restart by reinstantiating MemoryManager from same disk path.
    3. Create a new session.
    4. Retrieve memory.
    5. Verify memory exists and confidence/scope remain intact.
    """
    data_dir = test_env["data_dir"]
    mm1 = test_env["memory_mgr"]

    # 1. Store memory
    req = MemoryCreateRequest(
        scope=MemoryScope.GLOBAL.value,
        type=MemoryType.ARCHITECTURAL_RULE.value,
        content="Universal Agent Runtime must remain provider-agnostic",
        title="Universal Architecture Rule",
        source="USER",
        confidence=MemoryConfidence.USER_CONFIRMED.value,
        priority=MemoryPriority.CRITICAL.value
    )
    saved = mm1.create_memory(req)
    mem_id = saved.memory_id

    # 2. Simulate Application Restart (fresh MemoryManager and SessionManager instances)
    del mm1
    mm2 = MemoryManager(data_dir)
    sm2 = SessionManager(data_dir)

    # 3. New Session
    new_sess = sm2.create_session(display_name="Post-Restart Session")

    # 4 & 5. Verify retrieval and persistence
    loaded = mm2.get_memory(mem_id)
    assert loaded is not None
    assert loaded.content == "Universal Agent Runtime must remain provider-agnostic"
    assert loaded.confidence == MemoryConfidence.USER_CONFIRMED.value
    assert loaded.priority == MemoryPriority.CRITICAL.value
    assert loaded.scope == MemoryScope.GLOBAL.value

    # Verify JSON mirrors exist on disk
    assert (data_dir / "memory" / "global.json").exists()
    assert (data_dir / "memory" / "memory.db").exists()
    assert (data_dir / "memory" / "audit_events.json").exists()
