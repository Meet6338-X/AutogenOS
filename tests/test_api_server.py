"""
Integration tests for the complete FastAPI REST and WebSocket API server.
"""

import pytest
from starlette.testclient import TestClient
from autogenos.api.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "AutogenOS"
    assert data["status"] == "OPERATIONAL"
    assert "ToolAttentionEngine" in data["active_components"]


def test_api_tool_attention_gate(client):
    payload = {"query": "Inspect open windows and click buttons", "top_k": 2}
    response = client.post("/api/v1/tool-attention/gate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["promoted_tools"]) <= 2
    assert "mcp_tax_metrics" in data
    assert data["mcp_tax_metrics"]["tokens_saved"] > 0


def test_api_voice_endpoints(client):
    # Speak endpoint
    payload = {"text": "Test speech", "async_speak": True}
    res = client.post("/api/v1/voice/speak", json=payload)
    assert res.status_code == 200
    assert res.json()["mode"] == "100% LOCAL OFFLINE"

    # Stop endpoint
    res_stop = client.post("/api/v1/voice/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["stopped"] is True


def test_api_terminal_exec(client):
    payload = {"command": "python --version", "timeout": 10.0}
    response = client.post("/api/v1/terminal/exec", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["exit_code"] == 0


def test_api_os_endpoints(client):
    # Windows list
    res = client.get("/api/v1/os/windows")
    assert res.status_code == 200
    assert "windows" in res.json()

    # Active window
    res_act = client.get("/api/v1/os/active")
    assert res_act.status_code == 200

    # Screenshot
    res_shot = client.get("/api/v1/os/screenshot")
    assert res_shot.status_code == 200
    assert "dhash" in res_shot.json()


def test_api_livekit_status(client):
    res = client.get("/api/v1/livekit/status")
    assert res.status_code == 200
    data = res.json()
    assert "ws://127.0.0.1:7880" in data["url"]
    assert data["mode"] == "100% LOCAL FREE"


def test_api_explore(client):
    payload = {"targets": ["TextEditor", "Terminal"]}
    res = client.post("/api/v1/explore", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert "broad_tasks_explored" in data["metrics"]


def test_api_orchestrator_run(client):
    payload = {"intent": "Open calc and compute checksum"}
    res = client.post("/api/v1/orchestrator/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["phase"] == "COMPLETED"
    assert data["evidence_passed"] > 0
