"""
Comprehensive High-Performance FastAPI and WebSocket Server for AutogenOS.
Exposes internal modules and open-source components (MCP, Browser-Use, LiveKit) as callable APIs and WebSockets.
"""

from __future__ import annotations
import os
import sys
import time
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
from autogenos.components.mcp_bridge import AutogenOSMCPServer
from autogenos.components.browser_agent import BrowserAgent
from autogenos.components.livekit_bridge import LiveKitAgentBridge
from autogenos.self_improvement.self_trainer import SelfTrainingEngine, LoRATrainingConfig
from autogenos.core.system_doctor import SystemDoctor
from autogenos.eval.benchmark_harness import BenchmarkHarness

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
mcp_server = AutogenOSMCPServer()
browser_agent = BrowserAgent()
livekit_bridge = LiveKitAgentBridge(server=livekit_server)
self_trainer = SelfTrainingEngine()
doctor = SystemDoctor()
benchmark_harness = BenchmarkHarness()


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




class EvalRunRequest(BaseModel):
    suite: str = "all"  # "osworld", "agent-diff", "tool-attention", "all"
    output_file: Optional[str] = None


class TrainModelRequest(BaseModel):
    base_model: str = "meta-llama/Llama-3.2-3B-Instruct"
    mode: str = "DPO"
    epochs: int = 3
    learning_rate: float = 2e-4
    lora_r: int = 16
    lora_alpha: int = 32
    batch_size: int = 2
    output_adapter_dir: str = ".autogenos/adapters/autogenos_lora"

class ExploreRequest(BaseModel):
    targets: List[str] = Field(default_factory=lambda: ["TextEditor", "Terminal", "Settings"])


class MCPCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ScrapeRequest(BaseModel):
    url: Optional[str] = None
    html: Optional[str] = None


class LiveKitTokenRequest(BaseModel):
    room_name: str = "autogenos-room"
    identity: str = "user-client"


@app.get("/")
def get_root():
    return {
        "framework": "AutogenOS",
        "version": "0.1.0",
        "platform": os_ctrl.platform_name.upper(),
        "status": "OPERATIONAL",
        "livekit_local": livekit_server.get_connection_info(),
        "mcp_tools_available": len(mcp_server.get_supported_tools()),
        "active_components": [
            "ToolAttentionEngine",
            "SwarmGraphController (LangGraph)",
            "LocalWhisperSTT (faster-whisper)",
            "LocalTTS (SAPI5/Offline)",
            "TerminalRunner (RTK Compressed)",
            "ScreenVisionEngine (PIL IBTR)",
            "OSController (Native Accessibility)",
            "RSIAgent (Broad-then-Deep)",
            "AutogenOSMCPServer (Model Context Protocol)",
            "BrowserAgent (Browser-Use DOM-to-Markdown)",
            "LiveKitAgentBridge (Local WebRTC Rooms)",
            "SelfTrainingEngine (Autonomous DPO & Reflexion)"
        ]
    }


@app.post("/api/v1/orchestrator/run")
async def run_orchestrator(req: RunIntentRequest):
    """Executes long-horizon intent through full Planner-Actor-Verifier closed loop."""
    t0 = time.time()
    state = await swarm_controller.run_full_lifecycle(req.intent)
    try:
        self_trainer.process_completed_run(state, duration_sec=time.time() - t0)
    except Exception as e:
        logger.warning(f"Error recording trajectory in self_trainer: {e}")
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
        "metrics": metrics,
        "mcp_tax_metrics": metrics
    }


@app.get("/api/v1/mcp/tools")
def get_mcp_tools():
    """Lists all tools exposed by AutogenOS Model Context Protocol server."""
    return {"tools": mcp_server.get_supported_tools()}


@app.post("/api/v1/mcp/call")
def call_mcp_tool(req: MCPCallRequest):
    """Executes a tool call using the standard Model Context Protocol schema."""
    return mcp_server.handle_tools_call(req.name, req.arguments)


@app.post("/api/v1/mcp/jsonrpc")
def handle_mcp_jsonrpc(payload: Dict[str, Any]):
    """Standard JSON-RPC 2.0 endpoint for external MCP clients."""
    return mcp_server.process_jsonrpc_request(payload)


@app.post("/api/v1/browser/extract-markdown")
async def extract_page_markdown(req: ScrapeRequest):
    """Extracts clean structured Markdown and interactive UI targets from a URL or raw HTML."""
    if req.html:
        from autogenos.components.browser_agent import WebContentDistiller
        md = WebContentDistiller.html_to_markdown(req.html)
        interactive = [e.to_dict() for e in WebContentDistiller.extract_interactive_elements(req.html)]
        return {
            "url": req.url or "direct_html",
            "markdown": md,
            "interactive_elements": interactive,
            "interactive_count": len(interactive),
        }
    url = req.url or "about:blank"
    return await browser_agent.navigate_and_extract_markdown(url)


@app.post("/api/v1/livekit/token")
def generate_livekit_token(req: LiveKitTokenRequest):
    """Generates a 100% free local LiveKit WebRTC authentication token."""
    return livekit_bridge.get_connection_credentials(room_name=req.room_name, identity=req.identity)


@app.post("/api/v1/terminal/execute")
@app.post("/api/v1/terminal/exec")
def execute_terminal_cmd(req: TerminalExecRequest):
    """Executes arbitrary CLI command with token compression."""
    return terminal_runner.execute(req.command, cwd=req.cwd, timeout=req.timeout)


@app.get("/api/v1/os/windows")
def list_desktop_windows():
    """Lists visible windows across host OS."""
    return {"windows": os_ctrl.list_windows()}


@app.get("/api/v1/os/active-window")
@app.get("/api/v1/os/active")
def get_active_window():
    """Returns foreground window handle, title, and coordinates."""
    return os_ctrl.get_active_window()


@app.post("/api/v1/os/focus")
def focus_window_by_title(query: str):
    """Brings window matching title substring into focus."""
    success = os_ctrl.focus_window(query)
    return {"success": success, "query": query}


@app.post("/api/v1/os/click")
def click_coordinate(req: ClickRequest):
    """Injects hardware-level mouse click into OS."""
    success = os_ctrl.click_coordinate(req.x, req.y, req.button)
    return {"success": success, "x": req.x, "y": req.y}


@app.post("/api/v1/os/type")
def type_text(req: TypeRequest):
    """Injects hardware-level keystrokes into focused window."""
    success = os_ctrl.type_text(req.text)
    return {"success": success, "text": req.text}


@app.post("/api/v1/voice/speak")
def speak_local_tts(req: SpeakRequest):
    """Synthesizes zero-cost local speech via Windows SAPI5 or offline TTS."""
    success = local_tts.speak(req.text, asynchronous=req.async_speak)
    return {"success": success, "text": req.text, "mode": "100% LOCAL OFFLINE"}


@app.post("/api/v1/voice/stop")
def stop_voice():
    """Stops any currently active speech synthesis."""
    local_tts.stop()
    return {"stopped": True}


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


@app.get("/api/v1/self-improvement/metrics")
def get_self_training_metrics():
    """Returns real-time metrics on autonomous self-training, DPO datasets, and reflection rules."""
    return self_trainer.get_self_training_metrics()


@app.post("/api/v1/self-improvement/export-dataset")
def export_training_datasets(export_dir: str = ".autogenos/datasets"):
    """Exports causally grounded DPO preference pairs and SFT multi-turn datasets."""
    return self_trainer.export_training_datasets(export_dir=export_dir)


@app.get("/api/v1/self-improvement/rules")
def get_reflection_rules(query: Optional[str] = None):
    """Returns episodic memory rules and failure-prevention heuristics."""
    if query:
        rules = self_trainer.reflector.query_relevant_rules(query)
    else:
        rules = list(self_trainer.reflector.rules.values())
    return {"rules": [r.model_dump() for r in rules], "count": len(rules)}


@app.post("/api/v1/self-improvement/induce-tools")
def induce_reusable_tools(min_support: int = 2):
    """Mines recurring action sequences across trajectories and synthesizes new reusable MCP tools."""
    seqs = self_trainer.tool_inducer.identify_frequent_action_sequences(self_trainer.collector.trajectories, min_support=min_support)
    synthesized = [
        self_trainer.tool_inducer.synthesize_tool_scaffold(seq, f"auto_tool_{idx+1}")
        for idx, seq in enumerate(seqs)
    ]
    return {
        "frequent_sequences_count": len(seqs),
        "synthesized_tools": synthesized
    }




@app.get("/api/v1/system/doctor")
def run_system_doctor():
    """Executes comprehensive system diagnostics across OS bridges, MCP tools, and runtime."""
    return doctor.run_diagnostics().model_dump()


@app.get("/api/v1/eval/benchmarks")
def get_benchmarks():
    """Runs and returns comprehensive empirical benchmark results across OSWorld and AgentDiff."""
    report = benchmark_harness.run_all()
    return report.model_dump()


@app.post("/api/v1/eval/run")
def run_evaluation_suite(req: EvalRunRequest):
    """Executes a specific benchmark evaluation suite."""
    if req.suite.lower() == "all":
        report = benchmark_harness.run_all()
        return report.model_dump()
    else:
        res = benchmark_harness.run_suite(req.suite)
        return res.model_dump()


@app.post("/api/v1/self-improvement/train")
def train_model_adapter(req: TrainModelRequest):
    """Executes local LoRA / DPO model adapter training pass from collected execution trajectories."""
    cfg = LoRATrainingConfig(
        base_model=req.base_model,
        epochs=req.epochs,
        learning_rate=req.learning_rate,
        lora_r=req.lora_r,
        lora_alpha=req.lora_alpha,
        batch_size=req.batch_size,
        mode=req.mode,
        output_adapter_dir=req.output_adapter_dir
    )
    res = self_trainer.train_local_adapter(config=cfg)
    return res.model_dump()


@app.get("/api/v1/self-improvement/training-runs")
def get_training_runs():
    """Returns history of executed fine-tuning runs and adapter artifacts."""
    return {
        "training_runs": [r.model_dump() for r in self_trainer.training_runs],
        "count": len(self_trainer.training_runs)
    }


@app.websocket("/api/v1/voice/stream")
async def websocket_voice_stream(websocket: WebSocket):
    """Sub-500ms real-time voice streaming WebSocket."""
    await websocket.accept()
    from autogenos.voice.voice_agent import ContinuousVoiceAgent
    agent = ContinuousVoiceAgent()

    try:
        while True:
            data = await websocket.receive_json()
            intent = data.get("prompt", "System check")
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
