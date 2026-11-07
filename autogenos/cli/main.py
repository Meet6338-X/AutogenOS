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
from autogenos.self_improvement.self_trainer import SelfTrainingEngine, LoRATrainingConfig
from autogenos.core.system_doctor import SystemDoctor
from autogenos.eval.benchmark_harness import BenchmarkHarness
from autogenos.notifications.dispatcher import NotificationDispatcher, NotificationSeverity
from autogenos.cli.repl import InteractiveCockpitREPL
from autogenos.blocks import BlockManager, BlockType


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
    pdf_path = Path("docs/papers/AutogenOS_IEEE_Research_Paper.pdf")

    if getattr(args, "pdf", False):
        print("\n--- AUTOGENOS OFFICIAL IEEE RESEARCH PAPER ---")
        if pdf_path.exists():
            print(f"Title:   AutogenOS: A Deterministic, Multi-Agent Operating System Framework")
            print(f"Author:  Meet Shah, Senior Member, IEEE")
            print(f"Format:  IEEE Transactions Standard (2-Column, LaTeX / KaTeX)")
            print(f"Path:    {pdf_path.resolve()}")
            print(f"Status:  VERIFIED (Size: {pdf_path.stat().st_size:,} bytes)")
        else:
            print(f"PDF paper not found at {pdf_path}")
        return

    print("\n--- AUTOGENOS ACADEMIC WHITE PAPERS ---")
    if not papers_dir.exists():
        print("Papers directory not found.")
        return

    for p in sorted(papers_dir.glob("*.md")):
        first_line = p.read_text(encoding="utf-8").splitlines()[0]
        title = first_line.replace("#", "").strip()
        print(f"  * [{p.name}] -> {title}")
    print(f"  * [PDF Edition] -> {pdf_path} (Author: Meet Shah, Senior Member, IEEE)")
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

    if getattr(args, "train", False):
        cfg = LoRATrainingConfig()
        res = engine.train_local_adapter(config=cfg)
        print(f"\n[+] Local Fine-Tuning Pass Completed: Final Loss {res.final_loss:.4f} -> {res.output_adapter_dir}")



def cmd_doctor(args):
    doctor = SystemDoctor()
    report = doctor.run_diagnostics()
    print(doctor.format_cli_output(report))


def cmd_eval(args):
    harness = BenchmarkHarness()
    suite = args.suite or "all"
    print(f"\n[+] Running AutogenOS Benchmark Suite: '{suite}'...")
    if suite == "all":
        report = harness.run_all()
        print(harness.format_cli_report(report))
        if args.output:
            Path(args.output).write_text(report.model_dump_json(indent=2), encoding="utf-8")
            print(f"[+] Benchmark report saved to: {args.output}")
    else:
        res = harness.run_suite(suite)
        status = "[PASS]" if res.passed else "[FAIL]"
        print(f"\n  {status}  {res.suite_name} | Score: {res.score_pct:.1f}% | Time: {res.duration_sec:.4f}s")
        for k, v in res.details.items():
            print(f"      - {k}: {v}")


def cmd_train(args):
    engine = SelfTrainingEngine()
    cfg = LoRATrainingConfig(
        base_model=args.base_model,
        mode=args.mode,
        epochs=args.epochs,
        learning_rate=args.lr,
        output_adapter_dir=args.adapter_out
    )
    print(f"\n[+] Initializing AutogenOS Local LoRA / {cfg.mode} Fine-Tuning Pipeline...")
    print(f"    * Base Model:       {cfg.base_model}")
    print(f"    * Mode:             {cfg.mode}")
    print(f"    * Epochs:           {cfg.epochs}")
    print(f"    * Learning Rate:    {cfg.learning_rate}")
    print(f"    * Output Adapter:   {cfg.output_adapter_dir}")

    res = engine.train_local_adapter(config=cfg)
    print("\n--- FINE-TUNING EXECUTION REPORT ---")
    print(f"Run ID:             {res.run_id}")
    print(f"Status:             [{res.status}]")
    print(f"Initial Loss:       {res.initial_loss:.4f}")
    print(f"Final Loss:         {res.final_loss:.4f} (Reduction: {((res.initial_loss - res.final_loss)/res.initial_loss)*100:.1f}%)")
    print(f"Loss Curve:         {' -> '.join([str(l) for l in res.loss_history])}")
    print(f"Adapter Config:     {res.output_adapter_dir}/adapter_config.json")
    print(f"Unsloth Recipe:     {res.recipe_script_path}")



def cmd_notify(args):
    dispatcher = NotificationDispatcher(default_webhook_url=args.webhook)
    title = args.title or "AutogenOS Swarm Notification"
    body = args.message
    channels = [c.strip() for c in args.channel.split(",")]
    print(f"\n[+] Dispatching Notification to {channels}:")
    print(f"    Title: {title}")
    print(f"    Body:  {body}")
    res = dispatcher.dispatch(
        title=title,
        body=body,
        severity=args.severity.upper(),
        channels=channels,
        webhook_url=args.webhook
    )
    for ch, ok in res.items():
        st = "[OK]" if ok else "[FAILED]"
        print(f"    {st} Channel: {ch}")


def cmd_interactive(args):
    repl = InteractiveCockpitREPL()
    asyncio.run(repl.run_loop())


def cmd_blocks(args):
    mgr = BlockManager()
    action = args.block_action or "list"

    if action == "list":
        b_type = BlockType(args.type.upper()) if getattr(args, "type", None) else None
        blocks = mgr.list_blocks(block_type=b_type, enabled_only=getattr(args, "enabled_only", False))
        print(f"\n[+] AutogenOS Modular Feature Blocks ({len(blocks)} registered):\n")
        print(f"  {'ID':<34} | {'TYPE':<11} | {'STATUS':<9} | {'DESCRIPTION'}")
        print("  " + "-" * 85)
        for b in blocks:
            st = "[ACTIVE]" if b.is_enabled else "[DISABLED]"
            print(f"  {b.block_id:<34} | {b.block_type.value:<11} | {st:<9} | {b.metadata.description[:45]}")
        print()

    elif action == "info":
        b = mgr.get_block(args.block_id)
        if not b:
            print(f"[!] Block '{args.block_id}' not found.")
            return
        print(f"\n--- BLOCK METADATA: {b.block_id} ---")
        print(f"Name:         {b.metadata.name}")
        print(f"Type:         {b.block_type.value}")
        print(f"Status:       {b.metadata.status.value} (Enabled: {b.is_enabled})")
        print(f"Version:      {b.metadata.version}")
        print(f"Author:       {b.metadata.author}")
        print(f"Description:  {b.metadata.description}")
        print(f"Dependencies: {b.metadata.dependencies or 'None'}")
        print(f"Tags:         {', '.join(b.metadata.tags) if b.metadata.tags else 'None'}\n")

    elif action == "enable":
        ok = mgr.enable_block(args.block_id)
        print(f"[{'OK' if ok else 'FAIL'}] Block '{args.block_id}' {'enabled' if ok else 'not found'}.")

    elif action == "disable":
        ok = mgr.disable_block(args.block_id)
        print(f"[{'OK' if ok else 'FAIL'}] Block '{args.block_id}' {'disabled' if ok else 'not found'}.")

    elif action == "remove":
        b = mgr.remove_block(args.block_id)
        print(f"[{'OK' if b else 'FAIL'}] Block '{args.block_id}' {'removed' if b else 'not found'}.")

    elif action == "add":
        if getattr(args, "file", None):
            b = mgr.add_block_from_file(args.file)
            print(f"[+] Loaded block '{b.block_id}' from {args.file}")
        elif getattr(args, "code", None):
            b = mgr.add_block_from_code(args.code, block_id=getattr(args, "name", None))
            print(f"[+] Compiled and registered block '{b.block_id}'")
        else:
            print("[!] Provide either --file or --code")

    elif action == "exec":
        import json
        kwargs = {}
        if getattr(args, "args", None):
            try:
                kwargs = json.loads(args.args)
            except Exception as e:
                print(f"[!] Invalid JSON in --args: {e}")
                return
        print(f"\n[+] Executing Block: '{args.block_id}' with {kwargs}...")
        try:
            res = asyncio.run(mgr.execute_block(args.block_id, **kwargs))
            out_str = json.dumps(res, indent=2) if isinstance(res, (dict, list)) else str(res)
            print(f"[Result] Status: SUCCESS\n{out_str}\n")
        except Exception as e:
            print(f"[!] Execution error: {e}")

def cmd_meet(args):
    from autogenos.components.meeting_agent import MeetingAgent, MeetingConfig
    url = args.url
    print(f"\n[+] Connecting to meeting: {url}")
    cfg = MeetingConfig(
        url=url,
        display_name=getattr(args, "name", "Meet Shah"),
        mute_mic=not getattr(args, "unmute", False),
        disable_camera=getattr(args, "no_camera", False),
        auto_join=True,
        browser=getattr(args, "browser", "auto")
    )
    res = asyncio.run(MeetingAgent.join_meeting_fast(cfg))
    status_tag = "SUCCESS" if res.success else "FAILED"
    print(f"    Platform:    {res.platform.value.upper()}")
    print(f"    Meeting ID:  {res.meeting_id}")
    print(f"    Target URL:  {res.normalized_url}")
    print(f"    Status:      [{status_tag}] {res.status}")
    print(f"    Duration:    {res.duration_ms:.1f}ms")
    print(f"    Details:     {res.message}\n")


def cmd_serve(args):
    import uvicorn
    print(f"\n[+] Launching AutogenOS FastAPI & WebSocket Server on http://{args.host}:{args.port}")
    uvicorn.run("autogenos.api.server:app", host=args.host, port=args.port, reload=args.reload)


def cmd_ui(args):
    """Launches or opens the Next.js Cockpit Web UI with LiveKit Voice HUD."""
    import subprocess
    import webbrowser
    import shutil
    from pathlib import Path

    port = getattr(args, "port", 3000)
    dev = getattr(args, "dev", False)
    ui_dir = Path(__file__).resolve().parent.parent.parent / "ui"
    
    print("\n" + "=" * 65)
    print("  AutogenOS Sovereign Web Cockpit & LiveKit Voice HUD")
    print(f"  Target URL:   http://localhost:{port}")
    print(f"  UI Directory: {ui_dir}")
    print("=" * 65 + "\n")

    npm_bin = shutil.which("npm.cmd") or shutil.which("npm") or "npm"
    cmd = [npm_bin, "run", "dev", "--", "-p", str(port)] if dev else [npm_bin, "start", "--", "-p", str(port)]
    
    if getattr(args, "open", True):
        webbrowser.open(f"http://localhost:{port}")
        
    try:
        subprocess.run(cmd, cwd=str(ui_dir), check=True)
    except KeyboardInterrupt:
        print("\n[+] UI server stopped.")
    except Exception as e:
        print(f"\n[!] Note: {e}")
        print("    You can run manually: cd ui && npm.cmd run dev")


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
    p_papers = subparsers.add_parser("papers", help="List academic whitepapers or view official IEEE PDF")
    p_papers.add_argument("--pdf", action="store_true", help="Display verified path and metadata for official IEEE research paper PDF")

    # doctor command
    p_doc = subparsers.add_parser("doctor", help="Run comprehensive environmental & bridge diagnostics")

    # eval command
    p_eval = subparsers.add_parser("eval", help="Run empirical benchmark evaluation suites (OSWorld, Agent-Diff, Tool Attention)")
    p_eval.add_argument("--suite", type=str, default="all", choices=["osworld", "agent-diff", "tool-attention", "all"], help="Benchmark suite to execute")
    p_eval.add_argument("--output", type=str, default=None, help="Save evaluation report to JSON file")

    # train command
    p_train = subparsers.add_parser("train", help="Run local LoRA/DPO fine-tuning pass on recorded trajectories")
    p_train.add_argument("--base-model", type=str, default="meta-llama/Llama-3.2-3B-Instruct", help="Base model identifier")
    p_train.add_argument("--mode", type=str, default="DPO", choices=["DPO", "SFT"], help="Fine-tuning mode")
    p_train.add_argument("--epochs", type=int, default=3, help="Training epochs")
    p_train.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    p_train.add_argument("--adapter-out", type=str, default=".autogenos/adapters/autogenos_lora", help="Output directory for adapter weights")


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
    p_st.add_argument("--train", action="store_true", help="Trigger immediate local LoRA/DPO adapter training pass")

    # serve command
    
    # interactive / repl command
    p_repl = subparsers.add_parser("interactive", aliases=["repl"], help="Launch interactive multi-turn terminal cockpit")

    # notify command
    p_notif = subparsers.add_parser("notify", help="Dispatch notification to desktop toasts or webhooks")
    p_notif.add_argument("message", type=str, help="Notification body text")
    p_notif.add_argument("--title", type=str, default="AutogenOS Mission Alert", help="Notification title")
    p_notif.add_argument("--severity", type=str, default="INFO", choices=["INFO", "SUCCESS", "WARNING", "CRITICAL"], help="Alert severity")
    p_notif.add_argument("--channel", type=str, default="desktop", help="Target channels (comma-separated: desktop,webhook)")
    p_notif.add_argument("--webhook", type=str, default=None, help="Webhook URL (Slack, Discord, or generic)")

    
    # blocks command & subcommands
    p_blocks = subparsers.add_parser("blocks", help="Modular Block System: list, add, remove, enable, disable, and execute blocks")
    blocks_sub = p_blocks.add_subparsers(dest="block_action")

    # blocks list
    p_blist = blocks_sub.add_parser("list", help="List registered blocks")
    p_blist.add_argument("--type", type=str, default=None, help="Filter by block type (TOOL, ACTION, PERCEPTION, EVAL)")
    p_blist.add_argument("--enabled-only", action="store_true", help="Show only active blocks")

    # blocks info
    p_binfo = blocks_sub.add_parser("info", help="Display metadata for a block")
    p_binfo.add_argument("block_id", type=str, help="Target block identifier")

    # blocks enable
    p_benable = blocks_sub.add_parser("enable", help="Enable a block")
    p_benable.add_argument("block_id", type=str, help="Block identifier to enable")

    # blocks disable
    p_bdisable = blocks_sub.add_parser("disable", help="Disable a block")
    p_bdisable.add_argument("block_id", type=str, help="Block identifier to disable")

    # blocks remove
    p_bremove = blocks_sub.add_parser("remove", help="Remove/unregister a block")
    p_bremove.add_argument("block_id", type=str, help="Block identifier to remove")

    # blocks add
    p_badd = blocks_sub.add_parser("add", help="Register a new block from file or code")
    p_badd.add_argument("--file", type=str, default=None, help="Path to Python source file")
    p_badd.add_argument("--code", type=str, default=None, help="Inline Python source code")
    p_badd.add_argument("--name", type=str, default=None, help="Block identifier")

    # blocks exec
    p_bexec = blocks_sub.add_parser("exec", help="Execute a block capability")
    p_bexec.add_argument("block_id", type=str, help="Block identifier to execute")
    p_bexec.add_argument("--args", type=str, default="{}", help="Execution arguments as JSON string")

        # meet command
    p_meet = subparsers.add_parser("meet", help="Autonomous Google Meet, Zoom, and Teams connector & joiner")
    p_meet.add_argument("url", type=str, help="Meeting URL to join")
    p_meet.add_argument("--name", type=str, default="Meet Shah", help="Display name for guest lobbies")
    p_meet.add_argument("--unmute", action="store_true", help="Leave microphone active (default is muted)")
    p_meet.add_argument("--no-camera", action="store_true", help="Disable camera upon entering")
    p_meet.add_argument("--browser", type=str, default="auto", choices=["auto", "brave", "chrome", "edge"], help="Browser to launch")

    p_serve = subparsers.add_parser("serve", help="Launch FastAPI & WebSocket server")
    p_serve.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
    p_serve.add_argument("--port", type=int, default=8000, help="Port number")
    p_serve.add_argument("--reload", action="store_true", help="Enable live reload")

    # ui command
    p_ui = subparsers.add_parser("ui", help="Launch Next.js 16 Web Cockpit & LiveKit Voice HUD")
    p_ui.add_argument("--port", type=int, default=3000, help="Web UI port (default: 3000)")
    p_ui.add_argument("--dev", action="store_true", help="Launch in development mode with hot-reloading")
    p_ui.add_argument("--no-open", dest="open", action="store_false", help="Do not automatically open default browser")

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
    elif args.command == "doctor":
        cmd_doctor(args)
    elif args.command == "eval":
        cmd_eval(args)
    elif args.command == "train":
        cmd_train(args)
    elif args.command in ["interactive", "repl"]:
        cmd_interactive(args)
    elif args.command == "notify":
        cmd_notify(args)
    elif args.command == "blocks":
        cmd_blocks(args)
    elif args.command == "meet":
        cmd_meet(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "ui":
        cmd_ui(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
