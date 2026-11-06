"""
AutogenOS: Autonomous Multi-Agent Operating System Framework with Recursive Self-Improvement.

A high-performance Python library for autonomous desktop control, dynamic tool attention,
sub-500ms real-time voice, and verifier-gated multi-agent swarm execution.
"""

# Core & Swarm
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
from autogenos.swarm.graph import SwarmGraphController
from autogenos.swarm.planner import AutonomousIntentPlanner
from autogenos.swarm.postgres_saver import DurableStateSaver

# Execution & Dispatcher
from autogenos.execution.action_dispatcher import ActionDispatcher
from autogenos.execution.worktree_manager import WorktreeManager
from autogenos.execution.sandbox import ExecutionSandbox
from autogenos.execution.code_runner import MCPCodeRunner

# Tool Attention & Skills
from autogenos.tool_attention.engine import ToolAttentionEngine
from autogenos.tool_attention.registry import ToolMetadata, ToolRegistry
from autogenos.tool_attention.token_killer import TokenKiller
from autogenos.skills.progressive_loader import ProgressiveSkillLoader

# OS & Browser Control
from autogenos.control.os_controller import OSController
from autogenos.control.cdp_browser import CDPBrowserClient

# Voice & Real-Time Streams
from autogenos.voice.turn_detector import DynamicEMAEndpointing, TurnDetectorController
from autogenos.voice.voice_agent import ContinuousVoiceAgent

# Memory & Causal Verification
from autogenos.memory.carryon import CarryOnCompactor
from autogenos.memory.echopath import EchoPathReplayEngine, ActionNode
from autogenos.memory.ui_evol import UIEvolEngine
from autogenos.memory.struct_verifier import StructAgentVerifier

# Self-Improvement & Continuous Training
from autogenos.self_improvement.rsi_agent import RSIAgentEngine
from autogenos.self_improvement.self_trainer import (
    SelfTrainingEngine,
    TrajectoryCollector,
    PreferenceDatasetGenerator,
    EpisodicMemoryReflector,
    AutonomousToolInducer,
    ExecutionAttempt,
    TrajectoryRecord,
    DPOPreferencePair,
    SFTTrainingSample,
    ReflectionRule,
)

# Open-Source Bridges & Components
from autogenos.components.mcp_bridge import AutogenOSMCPServer, MCPClientBridge
from autogenos.components.browser_agent import BrowserAgent, WebContentDistiller, InteractiveElement
from autogenos.components.livekit_bridge import LiveKitAgentBridge, LiveKitTokenGenerator
from autogenos.components.livekit_local import LocalLiveKitServer
from autogenos.components.local_tts import LocalTTS
from autogenos.components.local_whisper import LocalWhisperSTT
from autogenos.components.screen_vision import ScreenVisionEngine
from autogenos.components.vector_search import LocalVectorStore
from autogenos.components.terminal_runner import TerminalRunner
from autogenos.components.browser_automation import LocalBrowserManager

# Evaluation & Gateway
from autogenos.eval.agent_diff import AgentDiffEvaluator
from autogenos.eval.osworld_runner import OSWorldEvaluationRunner
from autogenos.gateway.bifrost_client import BifrostGatewayClient, DualLayerSemanticCache

__version__ = "0.1.0"
__author__ = "Meet Shah"

__all__ = [
    # Core & Swarm
    "SwarmOrchestrator",
    "SwarmGlobalState",
    "SubTask",
    "TaskPhase",
    "ActionProposal",
    "DeterministicEvidence",
    "EvidenceType",
    "OrchestratorProtocol",
    "MASTER_OPERATIONAL_PROMPT",
    "SwarmGraphController",
    "AutonomousIntentPlanner",
    "DurableStateSaver",
    # Execution & Dispatcher
    "ActionDispatcher",
    "WorktreeManager",
    "ExecutionSandbox",
    "MCPCodeRunner",
    # Tool Attention
    "ToolAttentionEngine",
    "ToolMetadata",
    "ToolRegistry",
    "TokenKiller",
    "ProgressiveSkillLoader",
    # Control
    "OSController",
    "CDPBrowserClient",
    # Voice
    "DynamicEMAEndpointing",
    "TurnDetectorController",
    "ContinuousVoiceAgent",
    # Memory
    "CarryOnCompactor",
    "EchoPathReplayEngine",
    "ActionNode",
    "UIEvolEngine",
    "StructAgentVerifier",
    # Self-Improvement & Continuous Training
    "RSIAgentEngine",
    "SelfTrainingEngine",
    "TrajectoryCollector",
    "PreferenceDatasetGenerator",
    "EpisodicMemoryReflector",
    "AutonomousToolInducer",
    "ExecutionAttempt",
    "TrajectoryRecord",
    "DPOPreferencePair",
    "SFTTrainingSample",
    "ReflectionRule",
    # Open-Source Bridges & Components
    "AutogenOSMCPServer",
    "MCPClientBridge",
    "BrowserAgent",
    "WebContentDistiller",
    "InteractiveElement",
    "LiveKitAgentBridge",
    "LiveKitTokenGenerator",
    "LocalLiveKitServer",
    "LocalTTS",
    "LocalWhisperSTT",
    "ScreenVisionEngine",
    "LocalVectorStore",
    "TerminalRunner",
    "LocalBrowserManager",
    # Evaluation & Gateway
    "AgentDiffEvaluator",
    "OSWorldEvaluationRunner",
    "BifrostGatewayClient",
    "DualLayerSemanticCache",
]
