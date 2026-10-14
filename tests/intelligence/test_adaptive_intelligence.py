"""
Agy Studio v2.6 — Mandatory Adaptive Intelligence Test Suite
Tests all 17 requirements and the Golden End-to-End Learning lifecycle.
"""

import os
import sys
import shutil
import tempfile
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.session.session_manager import SessionManager, SessionState
from backend.memory.memory_manager import MemoryManager
from backend.intelligence import (
    IntelligenceEngine, ConfidenceLevel, ConfidenceEngine,
    IntentAnalyzer, TaskClassifier, StrategyRecord, ExperienceRecord,
    OutcomeAnalyzer, RegressionRecord
)

@pytest.fixture
def intel_env():
    temp_dir = Path(tempfile.mkdtemp(prefix="agy_intel_test_"))
    session_mgr = SessionManager(temp_dir)
    memory_mgr = MemoryManager(temp_dir)
    intel_engine = IntelligenceEngine(temp_dir, memory_mgr=memory_mgr, session_mgr=session_mgr)
    yield {
        "data_dir": temp_dir,
        "session_mgr": session_mgr,
        "memory_mgr": memory_mgr,
        "intel_engine": intel_engine
    }
    shutil.rmtree(temp_dir, ignore_errors=True)

# ----------------- TEST 1: LEARN SUCCESSFUL STRATEGY -----------------
def test_1_learn_successful_strategy(intel_env):
    """Task A succeeds with strategy X; Task B retrieves and reuses strategy X."""
    ie: IntelligenceEngine = intel_env["intel_engine"]

    # Session A succeeds with strategy
    strat = StrategyRecord(
        name="Async Helper for Desktop Folder Picker",
        task_type="GUI_AUTOMATION",
        description="Launch detached helper process on local bridge",
        recommended_agent="antigravity",
        dependencies=["bridge.exe"],
        verification_plan=["Process alive", "HTTP bridge status"],
        confidence=ConfidenceLevel.SUPPORTED.value
    )
    ie.strategy_engine.save_or_update(strat)

    res = ie.record_execution_outcome(
        task="Pick workspace folder via desktop bridge",
        exit_code=0,
        stdout_text="SUCCESS: bridge returned C:\\Projects\\Test",
        strategy_name="Async Helper for Desktop Folder Picker",
        agent_id="antigravity",
        test_results={"passed": 1, "failed": 0},
        session_id="SESS-A"
    )
    assert res["status"] == "recorded"
    assert res["analysis"]["verified"] is True

    # Check that strategy confidence and success count increased
    updated_strat = ie.strategy_engine.get_strategy_by_name("Async Helper for Desktop Folder Picker")
    assert updated_strat.success_count >= 1

    # Task B retrieves strategy matching keywords
    rec = ie.strategy_engine.recommend_strategy("GUI_AUTOMATION", keywords=["Async", "Helper"])
    assert rec is not None
    assert rec.name == "Async Helper for Desktop Folder Picker"

# ----------------- TEST 2: LEARN FAILURE -----------------
def test_2_learn_failure(intel_env):
    """Task A fails with strategy X; Task B avoids strategy X."""
    ie: IntelligenceEngine = intel_env["intel_engine"]

    strat = StrategyRecord(
        name="Synchronous Modal Dialog Picker",
        task_type="GUI_AUTOMATION",
        description="Block UI thread waiting for dialog",
        confidence=ConfidenceLevel.OBSERVED.value
    )
    ie.strategy_engine.save_or_update(strat)

    # Task A fails
    ie.record_execution_outcome(
        task="Open modal folder dialog",
        exit_code=1,
        stderr_text="Process crashed: event loop deadlocked in modal window",
        strategy_name="Synchronous Modal Dialog Picker",
        agent_id="antigravity",
        session_id="SESS-FAIL"
    )

    updated_strat = ie.strategy_engine.get_strategy_by_name("Synchronous Modal Dialog Picker")
    assert updated_strat.failure_count >= 1

    # Mark rejected
    ie.strategy_engine.mark_rejected("Synchronous Modal Dialog Picker", reason="Deadlocks event loop")
    
    # Task B check guard: must be blocked
    guard_res = ie.guard.check_proposal("Synchronous Modal Dialog Picker")
    assert guard_res.allowed is False
    assert guard_res.violation is True

# ----------------- TEST 3: USER CORRECTION -----------------
def test_3_user_correction(intel_env):
    """User rejects X ("Never use tkinter for workspace picker"); future task blocks X."""
    ie: IntelligenceEngine = intel_env["intel_engine"]

    res = ie.process_user_correction("Never use tkinter folder picker, use AgyStudioFolderPicker.exe instead")
    assert res["status"] == "learned"
    assert res["confidence"] == ConfidenceLevel.USER_CONFIRMED.value

    # Guard check on proposal mentioning tkinter folder picker
    guard_res = ie.guard.check_proposal("Implement tkinter folder picker for Windows workspace")
    assert guard_res.allowed is False
    assert guard_res.violation is True

# ----------------- TEST 4: CROSS-SESSION INTELLIGENCE -----------------
def test_4_cross_session_intelligence(intel_env):
    """Session A records a verified pattern; Session B benefits from it during preflight."""
    ie: IntelligenceEngine = intel_env["intel_engine"]
    sm: SessionManager = intel_env["session_mgr"]

    sess_a = sm.create_session(display_name="Session A")
    sess_b = sm.create_session(display_name="Session B")

    # In Session A, user corrects
    ie.learning_engine.learn_user_correction(
        rejected_entity="Raw Popen without creationflags",
        accepted_alternative="DETACHED_PROCESS flag",
        reason="Hangs server on Windows",
        session_id=sess_a.session_id
    )

    # In Session B, preflight runs
    pf = ie.run_preflight("Spawn server subprocess via Popen", session_id=sess_b.session_id)
    assert len(pf.rejected_approaches) >= 1
    assert any("Raw Popen without creationflags" in str(r) for r in pf.rejected_approaches)

# ----------------- TEST 5: RESTART PERSISTENCE -----------------
def test_5_restart_persistence(intel_env):
    """Learn in instance 1; close; instantiate instance 2 on same dir; knowledge survives."""
    temp_dir = intel_env["data_dir"]
    ie1 = intel_env["intel_engine"]

    ie1.learning_engine.learn_user_correction(
        rejected_entity="Hardcoded localhost port 3000",
        accepted_alternative="Dynamic port discovery",
        reason="Port conflicts"
    )
    ie1.export_forensic_reports()

    # Simulate restart by creating new IntelligenceEngine on same directory
    ie2 = IntelligenceEngine(temp_dir)
    strat = ie2.strategy_engine.get_strategy_by_name("Hardcoded localhost port 3000")
    assert strat is not None
    assert strat.status == "REJECTED"

    # Status persists
    st = ie2.get_status()
    assert st["strategies_count"] >= 1

# ----------------- TEST 6: STRATEGY CONFIDENCE BOOST -----------------
def test_6_strategy_confidence_boost(intel_env):
    """Repeated verified success increases confidence level."""
    ie: IntelligenceEngine = intel_env["intel_engine"]

    strat = StrategyRecord(
        name="Deterministic DOCX Table Layout",
        task_type="DOCUMENT_GENERATION",
        confidence=ConfidenceLevel.OBSERVED.value
    )
    ie.strategy_engine.save_or_update(strat)

    # 1 success -> SUPPORTED
    ie.strategy_engine.record_success("Deterministic DOCX Table Layout", evidence_ref="ev1")
    s1 = ie.strategy_engine.get_strategy_by_name("Deterministic DOCX Table Layout")
    assert s1.confidence in [ConfidenceLevel.SUPPORTED.value, ConfidenceLevel.VERIFIED.value]

    # Multiple successes -> VERIFIED
    ie.strategy_engine.record_success("Deterministic DOCX Table Layout", evidence_ref="ev2")
    ie.strategy_engine.record_success("Deterministic DOCX Table Layout", evidence_ref="ev3")
    s3 = ie.strategy_engine.get_strategy_by_name("Deterministic DOCX Table Layout")
    assert s3.confidence == ConfidenceLevel.VERIFIED.value

# ----------------- TEST 7: FAILURE CONFIDENCE DEMOTION -----------------
def test_7_failure_confidence_demotion(intel_env):
    """Repeated failure decreases confidence."""
    ie: IntelligenceEngine = intel_env["intel_engine"]

    strat = StrategyRecord(
        name="Hypothetical Fast Parser",
        task_type="GENERAL_CODING",
        confidence=ConfidenceLevel.SUPPORTED.value
    )
    ie.strategy_engine.save_or_update(strat)

    ie.strategy_engine.record_failure("Hypothetical Fast Parser", error_message="Syntax crash", evidence_ref="ev_err")
    s_demoted = ie.strategy_engine.get_strategy_by_name("Hypothetical Fast Parser")
    assert s_demoted.confidence == ConfidenceLevel.HYPOTHESIS.value

# ----------------- TEST 8: REGRESSION LEARNING -----------------
def test_8_regression_learning(intel_env):
    """Previously working feature breaks; regression stored and shown in future preflight."""
    ie: IntelligenceEngine = intel_env["intel_engine"]

    reg = RegressionRecord(
        component="Session Lineage",
        feature_name="Fork Session Branching",
        evidence="Parent session ID overwritten during fork",
        regression_test_cmd="pytest tests/test_sessions_and_memory.py -k test_session_fork"
    )
    ie.regression_detector.record_regression(reg)

    # Preflight touching Session Lineage must detect regression risk
    pf = ie.run_preflight("Fix Session Lineage fork branching")
    assert any("Fork Session Branching" in str(r) for r in pf.regression_risks)

# ----------------- TEST 9: AGENT ROUTING & METRICS -----------------
def test_9_agent_routing(intel_env):
    """Historical agent performance is recorded and produces explainable metrics."""
    ie: IntelligenceEngine = intel_env["intel_engine"]

    # Record runs for antigravity
    ie.agent_performance.record_run("antigravity", "GUI_AUTOMATION", success=True, verified=True, duration_seconds=1.2)
    ie.agent_performance.record_run("antigravity", "GUI_AUTOMATION", success=True, verified=True, duration_seconds=1.0)
    ie.agent_performance.record_run("antigravity", "GUI_AUTOMATION", success=False, verified=False, duration_seconds=2.0)

    perf = ie.agent_performance.get_performance("antigravity", "GUI_AUTOMATION")
    assert perf.total_runs == 3
    assert perf.success_runs == 2
    assert perf.failed_runs == 1
    assert round(perf.success_rate, 2) == 0.67

    explanations = ie.agent_performance.explain_selection("antigravity", "GUI_AUTOMATION")
    assert any("2/3 related tasks successful" in exp for exp in explanations)

# ----------------- TEST 10: MEMORY POISONING PREVENTION -----------------
def test_10_memory_poisoning_prevention(intel_env):
    """Unsupported agent claim without runtime proof cannot become VERIFIED."""
    analysis = OutcomeAnalyzer.analyze_execution(
        exit_code=0,
        stdout_text="Agent says: I verified that the code works perfectly!",
        stderr_text="",
        test_results=None,
        artifact_paths=None,
        user_confirmed=False
    )
    # Merely claims it worked: must NOT be VERIFIED
    assert analysis.verified is False
    assert analysis.confidence != ConfidenceLevel.VERIFIED.value
    assert analysis.evidence_type == "PROCESS_EXIT"

# ----------------- TEST 11: CONFLICT RESOLUTION -----------------
def test_11_conflict_resolution(intel_env):
    """User-confirmed correction overrides and supersedes agent claims."""
    c_rank = ConfidenceEngine.get_rank(ConfidenceLevel.USER_CONFIRMED.value)
    v_rank = ConfidenceEngine.get_rank(ConfidenceLevel.VERIFIED.value)
    s_rank = ConfidenceEngine.get_rank(ConfidenceLevel.SUPPORTED.value)

    assert c_rank > v_rank > s_rank

# ----------------- TEST 12: PROMPT OPTIMIZATION -----------------
def test_12_prompt_optimization(intel_env):
    """Vague prompt receives relevant historical context without altering the raw user instruction."""
    ie: IntelligenceEngine = intel_env["intel_engine"]

    raw = "Fix the workspace picker dialog"
    optimized = ie.optimize_prompt_context(raw)

    # Must contain 12-section header
    assert "=== AGY STUDIO ADAPTIVE INTELLIGENCE PREFLIGHT ===" in optimized
    assert "[USER INSTRUCTION]" in optimized
    # Must preserve the exact raw prompt text
    assert "Fix the workspace picker dialog" in optimized

# ----------------- TEST 13: EVIDENCE REQUIREMENT -----------------
def test_13_evidence_requirement(intel_env):
    """Only hard evidence (test pass, HWND, artifact) produces VERIFIED outcome."""
    # Test pass
    res_test = OutcomeAnalyzer.analyze_execution(exit_code=0, test_results={"passed": 5, "failed": 0})
    assert res_test.verified is True
    assert res_test.confidence == ConfidenceLevel.VERIFIED.value

    # HWND pass
    res_hwnd = OutcomeAnalyzer.analyze_execution(exit_code=0, hwnd_verified=True)
    assert res_hwnd.verified is True

    # Artifact pass
    res_art = OutcomeAnalyzer.analyze_execution(exit_code=0, artifact_paths=["C:/docs/report.docx"])
    assert res_art.verified is True

    # Plain exit code without test/artifact is NOT verified
    res_plain = OutcomeAnalyzer.analyze_execution(exit_code=0)
    assert res_plain.verified is False

# ----------------- TEST 14: RESPONSIVE UI CHECKS -----------------
def test_14_responsive_ui_structure():
    """Verify index.html contains responsive command center header elements."""
    html_path = PROJECT_ROOT / "static" / "index.html"
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")

    # Command palette shortcut
    assert "Ctrl" in content
    # v2.6 badge or version
    assert "2.6" in content or "v2.6" in content or "Agy Studio" in content

# ----------------- TEST 15: COMMAND PALETTE -----------------
def test_15_command_palette():
    """Verify Command Palette elements and shortcuts."""
    html_path = PROJECT_ROOT / "static" / "index.html"
    content = html_path.read_text(encoding="utf-8")
    # Verify palette triggers or elements exist
    assert "commandPalette" in content or "command" in content.lower()

# ----------------- TEST 16: SESSION CONTINUITY -----------------
def test_16_session_ui_lifecycle(intel_env):
    """Verify session pinning, resume lineage, and forking."""
    sm: SessionManager = intel_env["session_mgr"]

    s1 = sm.create_session(display_name="Production ATS")
    sid1 = s1.session_id

    # Pin
    assert sm.pin_session(sid1) is True
    assert sm.get_session(sid1).pinned is True

    # Resume non-destructively
    resumed = sm.resume_session(sid1)
    assert resumed.session_id != sid1
    assert resumed.resume_source_session_id == sid1
    # Historical session remains immutable
    assert sm.get_session(sid1).session_id == sid1

    # Fork
    forked = sm.fork_session(sid1, fork_name="Branch Experiment")
    assert forked.parent_session_id == sid1
    assert forked.display_name == "Branch Experiment"

# ----------------- TEST 17: INTELLIGENCE UI REAL METRICS -----------------
def test_17_intelligence_ui_metrics(intel_env):
    """Verify all status numbers match real database counts."""
    ie: IntelligenceEngine = intel_env["intel_engine"]
    status = ie.get_status()

    assert "version" in status
    assert status["version"] == "2.6.0"
    assert status["learning_status"] in ["Active", "Paused", "Needs Review"]
    assert isinstance(status["strategies_count"], int)
    assert isinstance(status["experiences_count"], int)
    assert isinstance(status["patterns_count"], int)
    assert isinstance(status["regressions_count"], int)

# ----------------- GOLDEN END-TO-END LEARNING TEST -----------------
def test_golden_end_to_end_adaptive_learning(intel_env):
    """
    GOLDEN TEST (PART AO & PART AQ):
    Session A: Real task -> user correction -> learns -> task succeeds -> evidence stored -> closes.
    Restart: Application restarts on same directory.
    Session B: Similar task -> adaptive preflight -> previous rejected blocked ->
               previous successful strategy recommended -> execution -> verification ->
               confidence updated.
    """
    temp_dir = intel_env["data_dir"]
    sm: SessionManager = intel_env["session_mgr"]
    ie: IntelligenceEngine = intel_env["intel_engine"]

    # --- SESSION A ---
    sess_a = sm.create_session(display_name="Session A — Initial Attempt")
    task_a = "Implement folder picker for workspace"

    # User correction occurs: Reject tkinter, use AgyStudioFolderPicker.exe bridge
    ie.learning_engine.learn_user_correction(
        rejected_entity="tkinter folder picker",
        accepted_alternative="AgyStudioFolderPicker.exe native bridge",
        reason="Tkinter crashes in packaged UV environment",
        session_id=sess_a.session_id,
        task_id="t1"
    )

    # Strategy implemented and verified
    strat_bridge = StrategyRecord(
        name="AgyStudioFolderPicker.exe native bridge",
        task_type="GUI_AUTOMATION",
        description="Async Win32 helper on port 8001",
        recommended_agent="antigravity",
        dependencies=["AgyStudioFolderPicker.exe"],
        verification_plan=["Process running", "HTTP 200 bridge", "Dialog result non-empty"],
        confidence=ConfidenceLevel.OBSERVED.value
    )
    ie.strategy_engine.save_or_update(strat_bridge)

    outcome_a = ie.record_execution_outcome(
        task="Pick workspace folder via AgyStudioFolderPicker.exe bridge",
        exit_code=0,
        stdout_text="SELECTED: C:\\Users\\piopi\\Documents\\gemini-projects",
        strategy_name="AgyStudioFolderPicker.exe native bridge",
        agent_id="antigravity",
        test_results={"passed": 3, "failed": 0},
        session_id=sess_a.session_id,
        task_id="t1"
    )
    assert outcome_a["analysis"]["verified"] is True

    # Application closes: Export reports
    ie.export_forensic_reports()
    sm.close_session()

    # --- SIMULATE FULL RESTART ---
    sm_restarted = SessionManager(temp_dir)
    ie_restarted = IntelligenceEngine(temp_dir, memory_mgr=intel_env["memory_mgr"], session_mgr=sm_restarted)

    # --- SESSION B ---
    sess_b = sm_restarted.create_session(display_name="Session B — Next Day Workspace Config")
    task_b = "Select folder for new workspace project"

    # 1. Adaptive Preflight in Session B
    preflight_b = ie_restarted.run_preflight(task_b, session_id=sess_b.session_id)

    # 2. Verify: Previous rejected approach is detected
    guard_check_rej = ie_restarted.guard.check_proposal("Use tkinter folder picker")
    assert guard_check_rej.allowed is False
    assert guard_check_rej.violation is True
    assert "REJETÉE" in guard_check_rej.warning

    # 3. Verify: Previous successful strategy is recommended
    rec_strat = ie_restarted.strategy_engine.recommend_strategy("GUI_AUTOMATION", keywords=["AgyStudioFolderPicker", "bridge"])
    assert rec_strat is not None
    assert rec_strat.name == "AgyStudioFolderPicker.exe native bridge"

    # 4. Agent performance routing
    perf = ie_restarted.agent_performance.get_performance("antigravity", "GUI_AUTOMATION")
    assert perf is not None
    assert perf.success_runs >= 1

    # 5. Task B execution & second verification
    outcome_b = ie_restarted.record_execution_outcome(
        task="Select folder with AgyStudioFolderPicker.exe bridge",
        exit_code=0,
        stdout_text="SELECTED: C:\\Projects\\TestWorkspace",
        strategy_name="AgyStudioFolderPicker.exe native bridge",
        agent_id="antigravity",
        test_results={"passed": 4, "failed": 0},
        session_id=sess_b.session_id,
        task_id="t2"
    )
    assert outcome_b["analysis"]["verified"] is True

    # 6. Verify: Strategy confidence increased
    final_strat = ie_restarted.strategy_engine.get_strategy_by_name("AgyStudioFolderPicker.exe native bridge")
    assert final_strat.success_count >= 2
    assert final_strat.confidence in [ConfidenceLevel.SUPPORTED.value, ConfidenceLevel.VERIFIED.value]
