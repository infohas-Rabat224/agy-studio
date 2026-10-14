import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient
from backend.server import app, session_manager, current_config

client = TestClient(app)

def test_config_language_and_hitl():
    res = client.post("/api/config", json={"language": "en", "hitl_mode": "strict"})
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "en"
    assert data["hitl_mode"] == "strict"

    # Reset back to fr
    res2 = client.post("/api/config", json={"language": "fr", "hitl_mode": "active"})
    assert res2.status_code == 200
    assert res2.json()["language"] == "fr"

def test_session_favorite_and_unfavorite():
    sess = session_manager.create_session(workspace=str(Path.cwd()), display_name="Test Fav Session")
    s_id = sess.session_id

    # Favorite
    fav_res = client.post(f"/api/sessions/{s_id}/favorite")
    assert fav_res.status_code == 200
    assert fav_res.json()["favorite"] is True
    assert session_manager.get_session(s_id).favorite is True

    # Unfavorite
    unfav_res = client.post(f"/api/sessions/{s_id}/unfavorite")
    assert unfav_res.status_code == 200
    assert unfav_res.json()["favorite"] is False
    assert session_manager.get_session(s_id).favorite is False

def test_hitl_assessment():
    # Dangerous command
    danger_res = client.post("/api/hitl/assess", json={"command": "git reset --hard HEAD~1"})
    assert danger_res.status_code == 200
    data = danger_res.json()
    assert data["is_high_risk"] is True
    assert data["risk_level"] == "CRITICAL"
    assert len(data["reasons"]) > 0

    # Safe command
    safe_res = client.post("/api/hitl/assess", json={"command": "git status"})
    assert safe_res.status_code == 200
    safe_data = safe_res.json()
    assert safe_data["is_high_risk"] is False
    assert safe_data["risk_level"] == "LOW"

def test_agent_duel():
    res = client.post("/api/agents/duel", json={
        "prompt": "write a fibonacci function",
        "agent_a": "antigravity",
        "agent_b": "claude"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "solution_a" in data
    assert "solution_b" in data
    assert data["solution_a"]["agent"] == "antigravity"
    assert data["solution_b"]["agent"] == "claude"

def test_session_report_and_pr():
    rep_res = client.get("/api/session/report")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert rep_data["status"] == "success"
    assert "markdown_report" in rep_data
    assert "📊 Rapport Exécutif" in rep_data["markdown_report"]

    pr_res = client.get("/api/session/pr-summary")
    assert pr_res.status_code == 200
    pr_data = pr_res.json()
    assert pr_data["status"] == "success"
    assert "pr_title" in pr_data
    assert "pr_body" in pr_data

def test_workspace_recent_files():
    res = client.get("/api/workspace/recent-files?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "files" in data
    assert isinstance(data["files"], list)
