"""
AutogenOS Interactive Terminal Cockpit & Natural Language REPL.
Provides an interactive multi-turn session with slash commands, live streaming telemetry,
and direct access to all internal subsystems (Doctor, Eval, LoRA Training, MCP, Voice, Blocks).
"""

from __future__ import annotations
import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

from autogenos.core.orchestrator import SwarmOrchestrator
from autogenos.swarm.graph import SwarmGraphController
from autogenos.core.system_doctor import SystemDoctor
from autogenos.eval.benchmark_harness import BenchmarkHarness
from autogenos.self_improvement.self_trainer import SelfTrainingEngine, LoRATrainingConfig
from autogenos.components.mcp_bridge import AutogenOSMCPServer
from autogenos.control.os_controller import OSController
from autogenos.components.local_tts import LocalTTS
from autogenos.blocks import BlockManager


class InteractiveCockpitREPL:
    """
    Interactive Terminal Shell for AutogenOS Multi-Agent Swarm.
    """

    def __init__(self):
        self.doctor = SystemDoctor()
        self.harness = BenchmarkHarness()
        self.self_trainer = SelfTrainingEngine()
        self.mcp_server = AutogenOSMCPServer()
        self.os_ctrl = OSController()
        self.tts = LocalTTS()
        self.block_manager = BlockManager()
        self.session_history = []

    def print_welcome(self):
        welcome = r"""
========================================================================
  AUTOGENOS INTERACTIVE TERMINAL COCKPIT (REPL v0.1.0)
  Type natural language goals or '/' slash commands. Type '/help' for list.
========================================================================
  Special Commands:
    /doctor        Run complete system diagnostics & bridge health check
    /eval          Run empirical benchmark suites (OSWorld, Agent-Diff)
    /train         Launch local LoRA/DPO model fine-tuning pass
    /meet <url>    Autonomous Google Meet, Zoom, or Teams joiner
    /blocks        List registered modular feature blocks
    /tools         List all native MCP tools (JSON-RPC 2.0)
    /status        Display host OS active window focus & accessibility
    /speak <text>  Speak text via 100% free local TTS
    /papers        View official IEEE research whitepaper metadata
    /clear         Clear terminal screen
    /exit          Exit interactive cockpit
========================================================================
"""
        print(welcome)

    def print_help(self):
        print("""
Available Slash Commands:
  /doctor          - Inspect Python, OS, Git long paths, CDP browser, and MCP tools
  /eval [suite]    - Run empirical benchmarks (osworld, agent-diff, tool-attention, all)
  /train [mode]    - Compile or execute local LoRA/DPO adapter pass
  /meet <url>      - Autonomous Google Meet, Zoom, or Teams joiner
  /blocks          - List and inspect registered modular feature blocks
  /tools           - Display active MCP tools catalog
  /status          - Host OS window title and accessibility tree status
  /speak <text>    - Synthesize local speech offline
  /papers          - IEEE whitepaper citations & PDF location
  /clear           - Clear terminal display
  /exit or /quit   - Terminate session
  <any text>       - Dispatch as natural language goal to Swarm Orchestrator
""")

    async def execute_goal(self, goal: str):
        print(f"\n[+] Dispatching to Swarm Graph: '{goal}'")

        def on_event(event_type: str, data: dict):
            if event_type == "PLANNER_COMPLETED":
                print(f"  [Planner] Decomposed into {data.get('subtasks_count')} atomic subtasks.")
            elif event_type == "ACTOR_PROPOSAL":
                st = "PASS" if data.get("evidence_passed") else "FAIL"
                print(f"  -> [Actor] Tool '{data.get('tool')}' [{st}]")
            elif event_type == "VERIFIER_COMMITTED":
                print(f"  ✓  [Verifier] COMMITTED: '{data.get('intent')}'")
            elif event_type == "VERIFIER_REJECTED":
                print(f"  ✗  [Verifier] REJECTED: '{data.get('intent')}' -> Repairing...")

        controller = SwarmGraphController(event_callback=on_event)
        state = await controller.run_full_lifecycle(goal)
        print(f"[Done] State: {state.phase.value} | Tokens Pruned: {state.token_usage_pruned}\n")
        self.session_history.append({"goal": goal, "phase": state.phase.value})

    async def run_loop(self):
        self.print_welcome()

        while True:
            try:
                user_input = input("autogenos> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[+] Exiting AutogenOS Cockpit. Goodbye.")
                break

            if not user_input:
                continue

            cmd_lower = user_input.lower()
            if cmd_lower in ["/exit", "/quit", "exit", "quit"]:
                print("[+] Exiting AutogenOS Cockpit. Goodbye.")
                break
            elif cmd_lower in ["/help", "help"]:
                self.print_help()
            elif cmd_lower == "/doctor":
                report = self.doctor.run_diagnostics()
                print(self.doctor.format_cli_output(report))
            elif cmd_lower.startswith("/eval"):
                parts = user_input.split(maxsplit=1)
                suite = parts[1] if len(parts) > 1 else "all"
                if suite == "all":
                    report = self.harness.run_all()
                    print(self.harness.format_cli_report(report))
                else:
                    try:
                        res = self.harness.run_suite(suite)
                        st = "[PASS]" if res.passed else "[FAIL]"
                        print(f"\n  {st} {res.suite_name} | Score: {res.score_pct:.1f}%")
                    except Exception as e:
                        print(f"[!] Error: {e}")
            elif cmd_lower.startswith("/train"):
                parts = user_input.split(maxsplit=1)
                mode = parts[1].upper() if len(parts) > 1 else "DPO"
                cfg = LoRATrainingConfig(mode=mode, epochs=2)
                res = self.self_trainer.train_local_adapter(config=cfg)
                print(f"\n[+] Fine-Tuning Completed [{res.mode}]: Loss {res.initial_loss:.4f} -> {res.final_loss:.4f}")
                print(f"    Adapter: {res.output_adapter_dir}\n")
            elif cmd_lower.startswith("/meet"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("[!] Usage: /meet <meeting_url>")
                else:
                    url = parts[1].strip()
                    from autogenos.components.meeting_agent import MeetingAgent, MeetingConfig
                    cfg = MeetingConfig(url=url, auto_join=True, mute_mic=True)
                    print(f"\n[+] Connecting to meeting: {url}...")
                    res = await MeetingAgent.join_meeting_fast(cfg)
                    st = "[SUCCESS]" if res.success else "[FAILED]"
                    print(f"  {st} {res.platform.value.upper()} ({res.meeting_id}) | Status: {res.status}")
                    print(f"  {res.message}\n")
            elif cmd_lower == "/blocks":
                blocks = self.block_manager.list_blocks()
                print(f"\n[+] Registered Feature Blocks ({len(blocks)} active):")
                for b in blocks:
                    st = "[ACTIVE]" if b.is_enabled else "[DISABLED]"
                    print(f"  * {b.block_id:<32} [{b.block_type.value:<10}] {st}")
                print()
            elif cmd_lower == "/tools":
                tools = self.mcp_server.get_supported_tools()
                print(f"\n[+] MCP Tools Catalog ({len(tools)} tools):")
                for t in tools:
                    print(f"  * {t['name']:<24} | {t['description']}")
                print()
            elif cmd_lower == "/status":
                win = self.os_ctrl.get_active_window()
                print(f"\nPlatform: {self.os_ctrl.platform_name.upper()} | Focus: '{win.get('title', 'Unknown')}'\n")
            elif cmd_lower.startswith("/speak"):
                text = user_input[6:].strip() or "AutogenOS operational."
                print(f"[+] Speaking: \"{text}\"")
                self.tts.speak(text, asynchronous=True)
            elif cmd_lower == "/papers":
                pdf = Path("docs/papers/AutogenOS_IEEE_Research_Paper.pdf")
                print(f"\n[+] IEEE Research Paper PDF: {pdf.resolve()} (Exists: {pdf.exists()})\n")
            elif cmd_lower == "/clear":
                os.system("cls" if os.name == "nt" else "clear")
            else:
                await self.execute_goal(user_input)
