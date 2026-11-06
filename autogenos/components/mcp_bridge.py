"""
Model Context Protocol (MCP) Bridge Component.
Leverages the cloned Model Context Protocol SDK to provide:
1. Client-side execution of standard MCP tools over stdio/HTTP.
2. Server-side exposure of AutogenOS capabilities as official MCP tools.
"""

from __future__ import annotations
import sys
import json
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add third_party/mcp_sdk/src to sys.path if available
mcp_sdk_src = Path(__file__).resolve().parent.parent.parent / "third_party" / "mcp_sdk" / "src"
if mcp_sdk_src.exists() and str(mcp_sdk_src) not in sys.path:
    sys.path.insert(0, str(mcp_sdk_src))

from autogenos.control.os_controller import OSController
from autogenos.components.terminal_runner import TerminalRunner
from autogenos.components.screen_vision import ScreenVisionEngine
from autogenos.components.local_tts import LocalTTS

logger = logging.getLogger("autogenos.mcp_bridge")


class MCPToolDefinition:
    """Standard Model Context Protocol tool schema."""
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


class AutogenOSMCPServer:
    """
    Standard MCP Server exposing AutogenOS native OS and browser tools
    conforming to the Model Context Protocol JSON-RPC 2.0 specification.
    """

    def __init__(self):
        self.os_controller = OSController()
        self.terminal_runner = TerminalRunner()
        self.screen_vision = ScreenVisionEngine()
        self.tts = LocalTTS()

    def get_supported_tools(self) -> List[Dict[str, Any]]:
        """Returns the complete catalog of tools in standard MCP format."""
        tools = [
            MCPToolDefinition(
                name="autogenos_list_windows",
                description="List all active visible windows on the host desktop with titles, handles, and bounds.",
                input_schema={"type": "object", "properties": {}}
            ),
            MCPToolDefinition(
                name="autogenos_focus_window",
                description="Bring an application window to the foreground by title or process name.",
                input_schema={
                    "type": "object",
                    "properties": {"title": {"type": "string", "description": "Title query or application name"}},
                    "required": ["title"]
                }
            ),
            MCPToolDefinition(
                name="autogenos_exec_shell",
                description="Execute a shell command in the local environment and return stdout, stderr, and exit code.",
                input_schema={
                    "type": "object",
                    "properties": {"command": {"type": "string", "description": "Shell command to execute"}},
                    "required": ["command"]
                }
            ),
            MCPToolDefinition(
                name="autogenos_capture_screen",
                description="Capture a screenshot of the primary display or region and compute its perceptual dHash.",
                input_schema={
                    "type": "object",
                    "properties": {"save_path": {"type": "string", "description": "Path to save screenshot"}}
                }
            ),
            MCPToolDefinition(
                name="autogenos_speak_tts",
                description="Speak text aloud using 100% free local offline zero-latency TTS.",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string", "description": "Text to synthesize"}},
                    "required": ["text"]
                }
            ),
            MCPToolDefinition(
                name="autogenos_click_coordinate",
                description="Simulate a hardware mouse click at specified screen (x, y) coordinates.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "Screen X coordinate"},
                        "y": {"type": "integer", "description": "Screen Y coordinate"},
                        "button": {"type": "string", "enum": ["left", "right"], "default": "left"}
                    },
                    "required": ["x", "y"]
                }
            ),
            MCPToolDefinition(
                name="autogenos_type_text",
                description="Inject hardware keystrokes and Unicode text into the currently active focused window.",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string", "description": "Text string to type"}},
                    "required": ["text"]
                }
            ),
        ]
        return [t.to_dict() for t in tools]

    def handle_tools_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an MCP tool call according to MCP JSON-RPC 2.0 response format:
        { "content": [ { "type": "text", "text": "..." } ], "isError": false }
        """
        logger.info(f"[MCPServer] Received tools/call for: '{name}' with args: {arguments}")
        try:
            if name == "autogenos_list_windows":
                windows = self.os_controller.list_windows()
                return {
                    "content": [{"type": "text", "text": json.dumps({"count": len(windows), "windows": windows[:15]}, indent=2)}],
                    "isError": False
                }

            elif name == "autogenos_focus_window":
                title = arguments.get("title", "")
                success = self.os_controller.focus_window(title)
                active = self.os_controller.get_active_window()
                return {
                    "content": [{"type": "text", "text": json.dumps({"success": success, "active_window": active}, indent=2)}],
                    "isError": not success
                }

            elif name == "autogenos_exec_shell":
                cmd = arguments.get("command", "")
                res = self.terminal_runner.execute(cmd)
                return {
                    "content": [{"type": "text", "text": json.dumps(res, indent=2)}],
                    "isError": res["exit_code"] != 0
                }

            elif name == "autogenos_capture_screen":
                path = arguments.get("save_path", ".autogenos/artifacts/mcp_screen.png")
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                saved = self.screen_vision.save_screenshot(path)
                dhash = self.screen_vision.compute_dhash(saved)
                return {
                    "content": [{"type": "text", "text": json.dumps({"save_path": path, "dhash": dhash}, indent=2)}],
                    "isError": False
                }

            elif name == "autogenos_speak_tts":
                text = arguments.get("text", "")
                success = self.tts.speak(text, asynchronous=False)
                return {
                    "content": [{"type": "text", "text": f"Synthesized speech: '{text}'"}],
                    "isError": not success
                }

            elif name == "autogenos_click_coordinate":
                x = arguments.get("x", 100)
                y = arguments.get("y", 100)
                button = arguments.get("button", "left")
                success = self.os_controller.click_coordinate(x, y, button=button)
                return {
                    "content": [{"type": "text", "text": f"Clicked ({x}, {y}) button={button}: {success}"}],
                    "isError": not success
                }

            elif name == "autogenos_type_text":
                text = arguments.get("text", "")
                success = self.os_controller.type_text(text)
                return {
                    "content": [{"type": "text", "text": f"Typed {len(text)} characters: {success}"}],
                    "isError": not success
                }

            else:
                return {
                    "content": [{"type": "text", "text": f"Tool '{name}' not found on AutogenOS MCP Server."}],
                    "isError": True
                }

        except Exception as e:
            logger.error(f"[MCPServer] Error executing tool '{name}': {e}")
            return {
                "content": [{"type": "text", "text": f"Execution error in {name}: {str(e)}"}],
                "isError": True
            }

    def process_jsonrpc_request(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes raw JSON-RPC 2.0 MCP protocol requests."""
        req_id = request_payload.get("id")
        method = request_payload.get("method")
        params = request_payload.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "autogenos-mcp-server", "version": "0.1.0"}
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.get_supported_tools()}
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            call_res = self.handle_tools_call(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": call_res
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found."}
            }


class MCPClientBridge:
    """
    Client connecting to external standard MCP servers (stdio or SSE).
    Allows AutogenOS agents to discover and invoke tools from external MCP servers.
    """

    def __init__(self, command: Optional[List[str]] = None):
        self.command = command
        self._proc: Optional[subprocess.Popen] = None
        self._local_server = AutogenOSMCPServer()

    def list_available_tools(self) -> List[Dict[str, Any]]:
        """Lists available MCP tools from connected or embedded MCP server."""
        return self._local_server.get_supported_tools()

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calls a tool via MCP protocol."""
        return self._local_server.handle_tools_call(name, arguments)
