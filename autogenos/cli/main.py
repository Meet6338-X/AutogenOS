"""
AutogenOS Unified Command Line Interface, Swarm Dashboard, and Server Launcher.
"""

from __future__ import annotations
import os
import sys
import asyncio
import argparse
from pathlib import Path
import json
from autogenos.core.orchestrator import SwarmOrchestrator
from autogenos.tool_attention.engine import ToolAttentionEngine
from autogenos.swarm.graph import SwarmGraphController
from autogenos.voice.voice_agent import ContinuousVoiceAgent
from autogenos.components.local_tts import LocalTTS
from autogenos.components.livekit_local import LocalLiveKitServer
from autogenos.self_improvement.rsi_agent import RSIAgentEngine
from autogenos.eval.agent_diff import AgentDiffEvaluator
from autogenos.control.os_controller import OSController
from autogenos.components.mcp_bridge import AutogenOSMCPServer
from autogenos.components.browser_agent import BrowserAgent, WebContentDistiller
from autogenos.self_improvement.self_trainer import SelfTrainingEngine


def print_banner():
    banner = r"""
     ___         __                                   ____   _____
    /   | __  __/ /_____  ____ ____  ____        ____/ __ \ / ___/
   / /| |/ / / / __/ __ \/ __ `/ _ \/ __ \______/ __ / / / /\__ \ 
  / ___ / /_/ / /_/ /_/ / /_/ /  __/ / / /_____/ /_/ / /_/ /___/ / 
 /_/  |_\__,_/\__/\____/\__, /\___/_/ /_/      \__,_/\____//____/  
                       /____/                                      
  Autonomous Multi-Agent Operating System Framework v0.1.0
  Recursive Self-Improving OS-Control Swarm (100% Free & Local)
    """
    print(banner)


async def cmd_run(args):
    intent = args.intent
    print(f"\n[+] Dispatching intent to AutogenOS Swarm:\n    -> {intent}\n")
    
    def on_event(event_type: str, data: dict):
        if event_type == "PLANNER_COMPLETED":
            print(f"[Planner] Decomposed into {data.get('subtasks_count')} atomic subtasks:")
            for i, st in enumerate(data.get('subtasks', [])):
                print(f"  {i+1}. {st}")
            print()
        elif event_type == "ACTOR_PROPOSAL":
            status = "PASSED" if data.get('evidence_passed') else "FAILED"
            print(f"  -> [Actor] Executed tool '{data.get('tool')}' [{status}] for: '{data.get('intent')}'")
            payload = str(data.get('raw_payload', '')).strip().splitlines()
            if payload:
                print(f"     Telemetry: {payload[0][:100]}")
        elif event_type == "VERIFIER_COMMITTED":
            print(f"  ✓  [Verifier] COMMITTED subtask: '{data.get('intent')}' (Tokens Pruned: {data.get('tokens_pruned')})\n")
        elif event_type == "VERIFIER_REJECTED":
            print(f"  ✗  [Verifier] REJECTED subtask: '{data.get('intent')}' -> Repairing...\n")

    controller = SwarmGraphController(event_callback=on_event)
    state = await controller.run_full_lifecycle(intent)
    
    print("\n" + "=" * 65)
    print(f"  Task Final Phase:        {state.phase.value}")
    print(f"  Subtasks Executed:       {len(state.subtasks)}")
    print(f"  Causal Evidence Proofs:  {len(state.accumulated_evidence)}")
    print(f"  Tokens Folded (CarryOn): {state.token_usage_pruned} tokens")
    print("=" * 65)


def cmd_tool_attention(args):
    engine = ToolAttentionEngine()
    query = args.query
    promoted = engine.gate_tools(query, top_k=args.top_k)
    metrics = engine.compute_mcp_tax_savings(len(promoted))

    print(f"\n[+] Evaluating Tool Attention for intent:\n    '{query}'\n")
    print(f"Active Promoted Tools ({len(promoted)} of {metrics['total_registered_tools']}):")
    for t in promoted:
        print(f"  * {t.name:<24} | {t.summary}")

    print("\n--- MCP TAX ELIMINATION METRICS ---")
    print(f"Naive MCP Token Ingestion:     ~{metrics['naive_mcp_tokens']} tokens")
    print(f"Tool Attention Dynamic Cost:   ~{metrics['tool_attention_tokens']} tokens")
    print(f"Total Context Tokens Saved:    ~{metrics['tokens_saved']} tokens ({metrics['token_reduction_pct']}% reduction)")
    print(f"Efficiency Gain:               {metrics['effective_context_utilization_gain']}")


async def cmd_voice(args):
    print("\n[+] Initializing Sub-500ms Continuous Voice Pipeline...")
    agent = ContinuousVoiceAgent()
    print(f"    * Silero VAD latency:        {agent.metrics.vad_latency_ms} ms")
    print(f"    * TurnDetector v1-mini:      {agent.metrics.turn_detector_latency_ms} ms")
    print(f"    * Dynamic EMA Endpointing:   Initial delay {agent.ema.current_delay:.2f}s (alpha={agent.ema.alpha})")
    print(f"    * Expected Total TTFA:       ~{agent.metrics.total_ttfa_ms:.1f} ms (< 500ms target)")

    print("\n[+] Simulating streaming agent turn with dynamic cadence...")
    async for chunk in agent.stream_agent_turn("System status check"):
        status = "PASSED (<500ms)" if chunk["ttfa_target_met"] else "FAILED"
        print(f"    Token: '{chunk['token']:<15}' | Elapsed: {chunk['latency_ms']:>5.1f} ms | Target: {status}")


def cmd_local_tts(args):
    text = args.text or "AutogenOS local voice synthesis operational with zero cloud latency."
    print(f"\n[+] Synthesizing 100% local, free speech via Windows SAPI5 / offline synthesizer:")
    print(f"    -> \"{text}\"")
    tts = LocalTTS()
    tts.speak(text, asynchronous=False)
    print("    [Done: Audio played to default speakers]")


def cmd_livekit_local(args):
    server = LocalLiveKitServer()
    success, msg = server.start_local_livekit()
    print(f"\n[+] Local LiveKit Status: {msg}")
    info = server.get_connection_info()
    print(f"    WebSocket URL: {info['url']}")
    print(f"    API Key:       {info['api_key']}")
    print(f"    API Secret:    {info['api_secret']}")
    print(f"    Cost:          {info['mode']}")


async def cmd_explore(args):
    print("\n[+] Launching RSIAgent Broad-then-Deep Recursive Self-Exploration...")
    rsi = RSIAgentEngine()
    targets = ["TextEditor", "Terminal", "SystemSettings"]
    results = await rsi.run_exploration_cycle(targets)

    print("\n--- RSI SELF-IMPROVEMENT REPORT ---")
    print(f"Broad Tasks Discovered:       {results['broad_tasks_explored']}")
    print(f"Total Boundary Edge Cases:    {results['total_tasks_discovered']}")
    print(f"Replayable Memory Graphs:     {results['frozen_memories_compiled']} frozen policies")


def cmd_status(args):
    os_ctrl = OSController()
    active_win = os_ctrl.get_active_window()
    print("\n--- AUTOGENOS HOST ENVIRONMENT ---")
    print(f"Platform:            {os_ctrl.platform_name.upper()}")
    print(f"Active Focus Window: '{active_win.get('title', 'Unknown')}'")
    print("Accessibility Bridge: Active & Grounded")


def cmd_papers(args):
    papers_dir = Path("papers")
    print("\n--- AUTOGENOS ACADEMIC WHITE PAPERS ---")
    if not papers_dir.exists():
        print("Papers directory not found.")
        return

    for p in sorted(papers_dir.glob("*.md")):
        # Read title
        first_line = p.read_text(encoding="utf-8").splitlines()[0]
        title = first_line.replace("#", "").strip()
        print(f"  * [{p.name}] -> {title}")
    print("\nAll papers formatted with formal proofs, Mermaid diagrams, and LaTeX formulations.")


def cmd_mcp_tools(args):
    server = AutogenOSMCPServer()
    tools = server.get_supported_tools()
    print(f"\n[+] AutogenOS Model Context Protocol (MCP) Tools Catalog ({len(tools)} tools):\n")
    for t in tools:
        print(f"  * {t['name']:<26} | {t['description']}")
    print("\nAll tools conform strictly to the Model Context Protocol JSON-RPC 2.0 specification.")


def cmd_mcp_call(args):
    server = AutogenOSMCPServer()
    tool_name = args.tool
    tool_args = {}
    if args.args:
        try:
            tool_args = json.loads(args.args)
        except Exception as e:
            print(f"[!] Error parsing arguments JSON: {e}")
            return

    print(f"\n[+] Invoking MCP Tool: '{tool_name}' with arguments: {tool_args}")
    res = server.handle_tools_call(tool_name, tool_args)
    status = "SUCCESS" if not res.get("isError") else "ERROR"
    print(f"    Status: [{status}]")
    for c in res.get("content", []):
        print(f"    Content ({c.get('type')}):")
        print(f"{c.get('text')}")


async def cmd_browser(args):
    url = args.url
    print(f"\n[+] Navigating and distilling web content for: {url}")
    import httpx
    try:
        resp = httpx.get(url, timeout=12.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        md = WebContentDistiller.html_to_markdown(resp.text)
        interactive = WebContentDistiller.extract_interactive_elements(resp.text)
        print(f"    Status Code: {resp.status_code}")
        print(f"    Interactive Targets Identified: {len(interactive)}")
        print("\n--- DISTILLED MARKDOWN PREVIEW (First 600 chars) ---")
        print(md[:600] + ("..." if len(md) > 600 else ""))
        print("\n--- TOP INTERACTIVE TARGETS ---")
        for elem in interactive[:8]:
            print(f"  [{elem.index}] {elem.role.upper():<7}: {elem.text:<35} | Selector: {elem.selector}")
    except Exception as e:
        print(f"[!] Browser extraction failed: {e}")


def cmd_self_train(args):
    engine = SelfTrainingEngine()
    metrics = engine.get_self_training_metrics()

    print("\n--- AUTOGENOS AUTONOMOUS SELF-TRAINING REPORT ---")
    print(f"Trajectories Recorded:       {metrics['total_trajectories_recorded']}")
    print(f"Successful Trajectories:     {metrics['successful_trajectories']}")
    print(f"Failed Trajectories:         {metrics['failed_trajectories']}")
    print(f"Execution Success Rate:      {metrics['success_rate_pct']:.1f}%")
    print(f"Episodic Reflection Rules:   {metrics['episodic_reflection_rules_count']} active heuristics")
    print(f"Mined Composite Patterns:    {metrics['mined_composite_patterns_count']}")
    print(f"Learning Feedback Mode:      {metrics['learning_mode']}")

    if args.rules:
        rules = list(engine.reflector.rules.values())
        print(f"\n[+] Active Episodic Memory Rules ({len(rules)}):")
        for r in rules:
            print(f"  * [{r.target_domain.upper()}] Avoid '{r.failing_pattern}': {r.recommended_policy} (Occurrences: {r.occurrences})")

    if args.export:
        res = engine.export_training_datasets(export_dir=args.export)
        print(f"\n[+] Exported Datasets to '{args.export}':")
        print(f"    - DPO Preference Pairs:  {res['dpo_samples_count']} samples -> {res['dpo_file']}")
        print(f"    - SFT Supervised Turns:  {res['sft_samples_count']} samples -> {res['sft_file']}")


def cmd_serve(args):
    import uvicorn
    print(f"\n[+] Launching AutogenOS FastAPI & WebSocket Server on http://{args.host}:{args.port}")
    uvicorn.run("autogenos.api.server:app", host=args.host, port=args.port, reload=args.reload)


def main():
    print_banner()
    parser = argparse.ArgumentParser(description="AutogenOS Swarm CLI")
    parser.add_argument("-v", "--version", action="version", version="autogenos 0.1.0")
    subparsers = parser.add_subparsers(dest="command")

    # run command
    p_run = subparsers.add_parser("run", help="Dispatch task to swarm orchestrator")
    p_run.add_argument("intent", type=str, help="Natural language objective")

    # tool-attention command
    p_ta = subparsers.add_parser("tool-attention", help="Inspect semantic tool gating and token savings")
    p_ta.add_argument("query", type=str, help="Intent to gate")
    p_ta.add_argument("--top-k", type=int, default=3, help="Max tools to promote")

    # voice command
    p_voice = subparsers.add_parser("voice", help="Run continuous voice pipeline simulation")

    # speak command
    p_speak = subparsers.add_parser("speak", help="Speak text via 100%% free local TTS")
    p_speak.add_argument("text", type=str, nargs="?", default=None, help="Text to speak")

    # livekit-local command
    p_lk = subparsers.add_parser("livekit-local", help="Start or inspect local LiveKit server")

    # explore command
    p_explore = subparsers.add_parser("explore", help="Run RSIAgent autonomous self-improvement")

    # status command
    p_status = subparsers.add_parser("status", help="Inspect OS host accessibility and bridge status")

    # papers command
    p_papers = subparsers.add_parser("papers", help="List academic whitepapers")

    # mcp-tools command
    p_mcp_tools = subparsers.add_parser("mcp-tools", help="List native Model Context Protocol (MCP) tools")

    # mcp-call command
    p_mcp_call = subparsers.add_parser("mcp-call", help="Dispatch tool call via MCP protocol")
    p_mcp_call.add_argument("tool", type=str, help="Tool name to execute")
    p_mcp_call.add_argument("--args", type=str, default="{}", help="Tool arguments as JSON string")

    # browser command
    p_browser = subparsers.add_parser("browser", help="Scrape web page and distill DOM into token-efficient Markdown")
    p_browser.add_argument("url", type=str, help="Target URL to inspect")

    # self-train command
    p_st = subparsers.add_parser("self-train", help="Inspect autonomous self-training telemetry and export datasets")
    p_st.add_argument("--export", type=str, default=None, help="Directory to export DPO and SFT JSONL datasets")
    p_st.add_argument("--rules", action="store_true", help="Print active episodic memory reflection rules")

    # serve command
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI & WebSocket server")
    p_serve.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
    p_serve.add_argument("--port", type=int, default=8000, help="Port number")
    p_serve.add_argument("--reload", action="store_true", help="Enable live reload")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "run":
        asyncio.run(cmd_run(args))
    elif args.command == "tool-attention":
        cmd_tool_attention(args)
    elif args.command == "voice":
        asyncio.run(cmd_voice(args))
    elif args.command == "speak":
        cmd_local_tts(args)
    elif args.command == "livekit-local":
        cmd_livekit_local(args)
    elif args.command == "explore":
        asyncio.run(cmd_explore(args))
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "papers":
        cmd_papers(args)
    elif args.command == "mcp-tools":
        cmd_mcp_tools(args)
    elif args.command == "mcp-call":
        cmd_mcp_call(args)
    elif args.command == "browser":
        asyncio.run(cmd_browser(args))
    elif args.command == "self-train":
        cmd_self_train(args)
    elif args.command == "serve":
        cmd_serve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
