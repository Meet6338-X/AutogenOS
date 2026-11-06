"""
AutogenOS: Autonomous Multi-Agent Operating System Framework with Recursive Self-Improvement.

A high-performance Python library for autonomous desktop control, dynamic tool attention,
sub-500ms real-time voice, and verifier-gated multi-agent swarm execution.
"""

from autogenos.core.orchestrator import SwarmOrchestrator
from autogenos.core.state import (
    SwarmGlobalState,
    SubTask,
    TaskPhase,
    ActionProposal,
    DeterministicEvidence,
    EvidenceType,
)
from autogenos.core.prompt_protocol import OrchestratorProtocol, MASTER_OPERATIONAL_PROMPT
from autogenos.tool_attention.engine import ToolAttentionEngine
from autogenos.tool_attention.registry import ToolMetadata, ToolRegistry
from autogenos.tool_attention.token_killer import TokenKiller
from autogenos.skills.progressive_loader import ProgressiveSkillLoader
from autogenos.execution.worktree_manager import WorktreeManager
from autogenos.execution.sandbox import ExecutionSandbox
from autogenos.execution.code_runner import MCPCodeRunner
from autogenos.control.os_controller import OSController
from autogenos.control.cdp_browser import CDPBrowserClient
from autogenos.swarm.graph import SwarmGraphController
from autogenos.swarm.postgres_saver import DurableStateSaver
from autogenos.voice.turn_detector import DynamicEMAEndpointing, TurnDetectorController
from autogenos.voice.voice_agent import ContinuousVoiceAgent
from autogenos.memory.carryon import CarryOnCompactor
from autogenos.memory.echopath import EchoPathReplayEngine, ActionNode
from autogenos.memory.ui_evol import UIEvolEngine
from autogenos.memory.struct_verifier import StructAgentVerifier
from autogenos.self_improvement.rsi_agent import RSIAgentEngine
from autogenos.eval.agent_diff import AgentDiffEvaluator
from autogenos.eval.osworld_runner import OSWorldEvaluationRunner
from autogenos.gateway.bifrost_client import BifrostGatewayClient, DualLayerSemanticCache
from autogenos.components.local_tts import LocalTTS
from autogenos.components.local_whisper import LocalWhisperSTT
from autogenos.components.livekit_local import LocalLiveKitServer
from autogenos.components.screen_vision import ScreenVisionEngine
from autogenos.components.vector_search import LocalVectorStore
from autogenos.components.terminal_runner import TerminalRunner
from autogenos.components.browser_automation import LocalBrowserManager

__version__ = "0.1.0"
__author__ = "Meet Shah"

__all__ = [
    "SwarmOrchestrator",
    "SwarmGlobalState",
    "SubTask",
    "TaskPhase",
    "ActionProposal",
    "DeterministicEvidence",
    "EvidenceType",
    "OrchestratorProtocol",
    "MASTER_OPERATIONAL_PROMPT",
    "ToolAttentionEngine",
    "ToolMetadata",
    "ToolRegistry",
    "TokenKiller",
    "ProgressiveSkillLoader",
    "WorktreeManager",
    "ExecutionSandbox",
    "MCPCodeRunner",
    "OSController",
    "CDPBrowserClient",
    "SwarmGraphController",
    "DurableStateSaver",
    "DynamicEMAEndpointing",
    "TurnDetectorController",
    "ContinuousVoiceAgent",
    "CarryOnCompactor",
    "EchoPathReplayEngine",
    "ActionNode",
    "UIEvolEngine",
    "StructAgentVerifier",
    "RSIAgentEngine",
    "AgentDiffEvaluator",
    "OSWorldEvaluationRunner",
    "BifrostGatewayClient",
    "DualLayerSemanticCache",
    "LocalTTS",
    "LocalWhisperSTT",
    "LocalLiveKitServer",
    "ScreenVisionEngine",
    "LocalVectorStore",
    "TerminalRunner",
    "LocalBrowserManager",
]
