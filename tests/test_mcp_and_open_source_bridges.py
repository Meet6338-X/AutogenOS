"""
Comprehensive unit and integration tests for AutogenOS Open-Source Bridges:
1. Model Context Protocol (MCP) JSON-RPC 2.0 Server & Client Bridge
2. Browser-Use DOM Distillation and Interactive Element Extraction
3. LiveKit Real-Time WebRTC Token Generation & Room Bridge
4. FastAPI Endpoints & ActionDispatcher Integration
"""

import json
import base64
import pytest
from starlette.testclient import TestClient

from autogenos.api.server import app
from autogenos.components.mcp_bridge import AutogenOSMCPServer, MCPToolDefinition
from autogenos.components.browser_agent import WebContentDistiller, InteractiveElement
from autogenos.components.livekit_bridge import LiveKitTokenGenerator, LiveKitAgentBridge
from autogenos.execution.action_dispatcher import ActionDispatcher


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# 1. Model Context Protocol (MCP) Server Tests
# ============================================================================

def test_mcp_server_supported_tools():
    server = AutogenOSMCPServer()
    tools = server.get_supported_tools()
    assert len(tools) >= 7
    tool_names = [t["name"] for t in tools]
    assert "autogenos_list_windows" in tool_names
    assert "autogenos_focus_window" in tool_names
    assert "autogenos_exec_shell" in tool_names
    assert "autogenos_capture_screen" in tool_names
    assert "autogenos_speak_tts" in tool_names
    assert "autogenos_click_coordinate" in tool_names
    assert "autogenos_type_text" in tool_names


def test_mcp_server_tool_call_list_windows():
    server = AutogenOSMCPServer()
    res = server.handle_tools_call("autogenos_list_windows", {})
    assert res["isError"] is False
    assert len(res["content"]) > 0
    text_payload = json.loads(res["content"][0]["text"])
    assert "count" in text_payload
    assert isinstance(text_payload["windows"], list)


def test_mcp_server_tool_call_exec_shell():
    server = AutogenOSMCPServer()
    res = server.handle_tools_call("autogenos_exec_shell", {"command": "echo MCP_BRIDGE_ONLINE"})
    assert res["isError"] is False
    text_payload = json.loads(res["content"][0]["text"])
    assert text_payload["exit_code"] == 0
    assert "MCP_BRIDGE_ONLINE" in text_payload["stdout"]


def test_mcp_server_tool_call_speak_tts():
    server = AutogenOSMCPServer()
    res = server.handle_tools_call("autogenos_speak_tts", {"text": "MCP Voice Verification"})
    assert res["isError"] is False
    assert "Synthesized speech" in res["content"][0]["text"]


def test_mcp_server_unknown_tool():
    server = AutogenOSMCPServer()
    res = server.handle_tools_call("non_existent_tool_xyz", {})
    assert res["isError"] is True
    assert "not found" in res["content"][0]["text"]


def test_mcp_server_jsonrpc_initialize():
    server = AutogenOSMCPServer()
    rpc_req = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "initialize",
        "params": {}
    }
    rpc_res = server.process_jsonrpc_request(rpc_req)
    assert rpc_res["jsonrpc"] == "2.0"
    assert rpc_res["id"] == "1"
    assert "protocolVersion" in rpc_res["result"]
    assert rpc_res["result"]["serverInfo"]["name"] == "autogenos-mcp-server"


def test_mcp_server_jsonrpc_tools_list():
    server = AutogenOSMCPServer()
    rpc_req = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/list",
        "params": {}
    }
    rpc_res = server.process_jsonrpc_request(rpc_req)
    assert rpc_res["id"] == "2"
    assert "tools" in rpc_res["result"]
    assert len(rpc_res["result"]["tools"]) >= 7


def test_mcp_server_jsonrpc_tools_call():
    server = AutogenOSMCPServer()
    rpc_req = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tools/call",
        "params": {
            "name": "autogenos_exec_shell",
            "arguments": {"command": "echo JSONRPC_CALL_SUCCESS"}
        }
    }
    rpc_res = server.process_jsonrpc_request(rpc_req)
    assert rpc_res["id"] == "3"
    assert rpc_res["result"]["isError"] is False
    assert "JSONRPC_CALL_SUCCESS" in rpc_res["result"]["content"][0]["text"]


def test_mcp_server_jsonrpc_unknown_method():
    server = AutogenOSMCPServer()
    rpc_req = {
        "jsonrpc": "2.0",
        "id": "4",
        "method": "unsupported/method",
        "params": {}
    }
    rpc_res = server.process_jsonrpc_request(rpc_req)
    assert "error" in rpc_res
    assert rpc_res["error"]["code"] == -32601


# ============================================================================
# 2. Browser-Use DOM Distiller & Interactive Element Extraction
# ============================================================================

def test_browser_content_distiller_markdown():
    sample_html = """
    <html>
      <head>
        <title>AutogenOS Test Page</title>
        <script>console.log("noisy script");</script>
        <style>body { color: red; }</style>
      </head>
      <body>
        <h1>Main Header</h1>
        <h2>Sub Section</h2>
        <p>This is a test paragraph describing the architecture.</p>
        <a href="https://autogenos.org/docs">Documentation Link</a>
        <button>Submit Proposal</button>
        <ul>
          <li>Item 1</li>
          <li>Item 2</li>
        </ul>
      </body>
    </html>
    """
    md = WebContentDistiller.html_to_markdown(sample_html)
    assert "# Main Header" in md
    assert "## Sub Section" in md
    assert "[Documentation Link](https://autogenos.org/docs)" in md
    assert "[Button: Submit Proposal]" in md
    assert "* Item 1" in md
    assert "* Item 2" in md
    assert "noisy script" not in md
    assert "color: red" not in md


def test_browser_interactive_element_extraction():
    sample_html = """
    <div>
      <a href="https://example.com/login">Login Anchor</a>
      <button>Click Here</button>
      <input type="text" name="username" placeholder="Enter username" />
      <input type="password" name="password" />
    </div>
    """
    elements = WebContentDistiller.extract_interactive_elements(sample_html)
    assert len(elements) == 4
    roles = [e.role for e in elements]
    assert "button" in roles
    assert "input" in roles
    assert "link" in roles


# ============================================================================
# 3. LiveKit Real-Time WebRTC Bridge & Token Generator
# ============================================================================

def test_livekit_token_generator_jwt():
    token = LiveKitTokenGenerator.create_token(
        api_key="test-key",
        api_secret="test-secret-123456",
        identity="agent-worker-01",
        room_name="swarm-room-alpha"
    )
    parts = token.split(".")
    assert len(parts) == 3

    # Decode payload
    def decode_b64(seg: str) -> dict:
        pad = len(seg) % 4
        if pad != 0:
            seg += "=" * (4 - pad)
        return json.loads(base64.urlsafe_b64decode(seg).decode("utf-8"))

    header = decode_b64(parts[0])
    payload = decode_b64(parts[1])

    assert header["alg"] == "HS256"
    assert payload["iss"] == "test-key"
    assert payload["sub"] == "agent-worker-01"
    assert payload["video"]["room"] == "swarm-room-alpha"
    assert payload["video"]["roomJoin"] is True


def test_livekit_agent_bridge_credentials():
    bridge = LiveKitAgentBridge()
    creds = bridge.get_connection_credentials(room_name="test-room", identity="tester")
    assert creds["room_name"] == "test-room"
    assert creds["room"] == "test-room"
    assert creds["identity"] == "tester"
    assert "token" in creds
    assert creds["mode"] == "100% Free & Local"


# ============================================================================
# 4. FastAPI Endpoints Integration
# ============================================================================

def test_api_mcp_tools_catalog(client):
    res = client.get("/api/v1/mcp/tools")
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    assert len(data["tools"]) >= 7


def test_api_mcp_call(client):
    res = client.post("/api/v1/mcp/call", json={
        "name": "autogenos_exec_shell",
        "arguments": {"command": "echo FASTAPI_MCP_DISPATCH"}
    })
    assert res.status_code == 200
    data = res.json()
    assert data["isError"] is False
    assert "FASTAPI_MCP_DISPATCH" in data["content"][0]["text"]


def test_api_mcp_jsonrpc_endpoint(client):
    payload = {
        "jsonrpc": "2.0",
        "id": "api-rpc-1",
        "method": "tools/list",
        "params": {}
    }
    res = client.post("/api/v1/mcp/jsonrpc", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "api-rpc-1"
    assert "tools" in data["result"]


def test_api_browser_extract_markdown(client):
    sample_html = "<html><body><h1>Hello AutogenOS</h1><p>Documentation paragraph.</p></body></html>"
    res = client.post("/api/v1/browser/extract-markdown", json={"html": sample_html})
    assert res.status_code == 200
    data = res.json()
    assert "# Hello AutogenOS" in data["markdown"]
    assert "interactive_elements" in data


def test_api_livekit_token(client):
    res = client.post("/api/v1/livekit/token", json={
        "room_name": "executive-bridge",
        "identity": "human-supervisor"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["room"] == "executive-bridge"
    assert data["identity"] == "human-supervisor"
    assert "token" in data
    assert len(data["token"].split(".")) == 3


# ============================================================================
# 5. ActionDispatcher Real Dispatch Execution
# ============================================================================

def test_action_dispatcher_mcp_tool_call():
    dispatcher = ActionDispatcher()
    res, evidence = dispatcher.execute_tool("mcp_call_tool", {
        "name": "autogenos_exec_shell",
        "arguments": {"command": "echo ACTION_DISPATCHER_MCP_PASS"}
    })
    assert evidence.passed is True
    assert res["isError"] is False
    assert "ACTION_DISPATCHER_MCP_PASS" in res["content"][0]["text"]


def test_action_dispatcher_livekit_token_generation():
    dispatcher = ActionDispatcher()
    res, evidence = dispatcher.execute_tool("livekit_generate_token", {
        "room_name": "swarm-collab",
        "identity": "agent-orchestrator"
    })
    assert evidence.passed is True
    assert "token" in res
    assert res["room"] == "swarm-collab"
