"""
Comprehensive High-Performance FastAPI and WebSocket Server for AutogenOS.
Exposes every internal module and open-source component as a callable API and WebSocket service.
"""

from __future__ import annotations
import base64
import asyncio
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from autogenos.core.orchestrator import SwarmOrchestrator
from autogenos.swarm.graph import SwarmGraphController
from autogenos.tool_attention.engine import ToolAttentionEngine
from autogenos.components.local_whisper import LocalWhisperSTT
from autogenos.components.local_tts import LocalTTS
from autogenos.components.terminal_runner import TerminalRunner
from autogenos.components.screen_vision import ScreenVisionEngine
from autogenos.components.livekit_local import LocalLiveKitServer
from autogenos.control.os_controller import OSController
from autogenos.self_improvement.rsi_agent import RSIAgentEngine
from autogenos.eval.agent_diff import AgentDiffEvaluator, StateSnapshot

logger = logging.getLogger("autogenos.api")

app = FastAPI(
    title="AutogenOS Swarm & System Control API",
    description="High-performance REST & WebSocket API for autonomous multi-agent operating system swarm",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared component singletons
tool_engine = ToolAttentionEngine()
terminal_runner = TerminalRunner()
screen_vision = ScreenVisionEngine()
local_tts = LocalTTS()
local_stt = LocalWhisperSTT()
os_ctrl = OSController()
livekit_server = LocalLiveKitServer()
swarm_controller = SwarmGraphController(tool_engine=tool_engine)
rsi_engine = RSIAgentEngine()


# Request / Response Schemas
class RunIntentRequest(BaseModel):
    intent: str
    max_steps: int = 15


class ToolGateRequest(BaseModel):
    query: str
    top_k: int = 3


class SpeakRequest(BaseModel):
    text: str
    async_speak: bool = True


class TerminalExecRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout: float = 30.0


class ClickRequest(BaseModel):
    x: int
    y: int
    button: str = "left"


class TypeRequest(BaseModel):
    text: str


class ExploreRequest(BaseModel):
    targets: List[str] = Field(default_factory=lambda: ["TextEditor", "Terminal", "Settings"])


@app.get("/")
def get_root():
    return {
        "framework": "AutogenOS",
        "version": "0.1.0",
        "platform": os_ctrl.platform_name.upper(),
        "status": "OPERATIONAL",
        "livekit_local": livekit_server.get_connection_info(),
        "active_components": [
            "ToolAttentionEngine",
            "SwarmGraphController (LangGraph)",
            "LocalWhisperSTT (faster-whisper)",
            "LocalTTS (SAPI5/Offline)",
            "TerminalRunner (RTK Compressed)",
            "ScreenVisionEngine (PIL IBTR)",
            "OSController (Native Accessibility)",
            "RSIAgent (Broad-then-Deep)"
        ]
    }


@app.post("/api/v1/orchestrator/run")
async def run_orchestrator(req: RunIntentRequest):
    """Executes long-horizon intent through full Planner-Actor-Verifier closed loop."""
    state = await swarm_controller.run_full_lifecycle(req.intent)
    return {
        "session_id": state.session_id,
        "phase": state.phase.value,
        "subtasks_total": len(state.subtasks),
        "evidence_passed": len(state.accumulated_evidence),
        "tokens_pruned": state.token_usage_pruned,
        "subtasks": [
            {
                "id": s.subtask_id,
                "intent": s.intent,
                "phase": s.phase.value,
                "is_committed": s.is_committed
            }
            for s in state.subtasks
        ]
    }


@app.post("/api/v1/tool-attention/gate")
def gate_tools(req: ToolGateRequest):
    """Computes semantic Tool Attention gating and calculates MCP Tax savings."""
    promoted = tool_engine.gate_tools(req.query, top_k=req.top_k)
    metrics = tool_engine.compute_mcp_tax_savings(len(promoted))
    return {
        "query": req.query,
        "promoted_tools": [
            {
                "name": t.name,
                "summary": t.summary,
                "tags": t.tags,
                "parameters": t.parameters_schema
            }
            for t in promoted
        ],
        "mcp_tax_metrics": metrics
    }


@app.post("/api/v1/voice/speak")
def speak_text(req: SpeakRequest):
    """Speaks text through local zero-cost TTS (Windows SAPI5 or offline synthesizer)."""
    success = local_tts.speak(req.text, asynchronous=req.async_speak)
    return {"spoken": success, "text": req.text, "mode": "100% LOCAL OFFLINE"}


@app.post("/api/v1/voice/stop")
def stop_speaking():
    """Barge-in interrupt: instantly halts TTS playback."""
    local_tts.stop()
    return {"stopped": True}


@app.post("/api/v1/terminal/exec")
def execute_terminal(req: TerminalExecRequest):
    """Executes shell command with real-time output and RTK token compression."""
    result = terminal_runner.execute(req.command, cwd=req.cwd, timeout=req.timeout)
    return result


@app.get("/api/v1/os/windows")
def list_open_windows():
    """Enumerates visible top-level windows on host system."""
    windows = os_ctrl.list_windows()
    return {"count": len(windows), "windows": windows}


@app.get("/api/v1/os/active")
def get_active_window():
    """Gets details and coordinates of currently focused window."""
    return os_ctrl.get_active_window()


@app.post("/api/v1/os/click")
def click_mouse(req: ClickRequest):
    """Injects hardware-level mouse click."""
    success = os_ctrl.click_coordinate(req.x, req.y, req.button)
    return {"success": success, "x": req.x, "y": req.y, "button": req.button}


@app.post("/api/v1/os/type")
def type_keystrokes(req: TypeRequest):
    """Injects hardware keystrokes."""
    success = os_ctrl.type_text(req.text)
    return {"success": success, "text": req.text}


@app.get("/api/v1/os/screenshot")
def capture_screenshot():
    """Captures desktop frame and returns base64 PNG data."""
    img = screen_vision.capture_fullscreen()
    import io
    buff = io.BytesIO()
    img.save(buff, format="PNG")
    b64_str = base64.b64encode(buff.getvalue()).decode("utf-8")
    dhash = screen_vision.compute_dhash(img)
    return {
        "width": img.width,
        "height": img.height,
        "dhash": dhash,
        "image_base64": b64_str[:120] + "... [truncated]"
    }


@app.post("/api/v1/explore")
async def trigger_rsi_exploration(req: ExploreRequest):
    """Executes RSIAgent Broad-then-Deep autonomous exploration cycle."""
    results = await rsi_engine.run_exploration_cycle(req.targets)
    return {
        "status": "COMPLETED",
        "metrics": results
    }


@app.get("/api/v1/livekit/status")
def get_livekit_status():
    """Returns local LiveKit zero-cost configuration info."""
    return livekit_server.get_connection_info()


@app.websocket("/api/v1/voice/stream")
async def websocket_voice_stream(websocket: WebSocket):
    """
    Sub-500ms real-time voice streaming WebSocket.
    Clients send audio/text frames and receive streaming tokens and synthesized audio chunks.
    """
    await websocket.accept()
    from autogenos.voice.voice_agent import ContinuousVoiceAgent
    agent = ContinuousVoiceAgent()

    try:
        while True:
            data = await websocket.receive_json()
            intent = data.get("prompt", "System check")
            
            # Stream response chunks with sub-500ms TTFA
            async for chunk in agent.stream_agent_turn(intent):
                await websocket.send_json(chunk)
    except WebSocketDisconnect:
        logger.info("Voice streaming WebSocket disconnected.")


@app.websocket("/api/v1/swarm/telemetry")
async def websocket_swarm_telemetry(websocket: WebSocket):
    """Real-time event feed for live execution dashboards."""
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(2.0)
            telemetry = {
                "active_window": os_ctrl.get_active_window().get("title", ""),
                "pruned_tokens": swarm_controller.compactor.total_tokens_pruned,
                "replayed_paths": len(rsi_engine.frozen_experience_catalog),
                "timestamp": asyncio.get_event_loop().time()
            }
            await websocket.send_json(telemetry)
    except WebSocketDisconnect:
        pass
