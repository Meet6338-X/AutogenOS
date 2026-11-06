// AutogenOS Studio Precision Interactive Engine

document.addEventListener("DOMContentLoaded", () => {
  initCursorSpotlight();
  initSwarmCockpit();
  initToolAttentionBenchmarker();
  initStudioOscilloscope();
  initPlaygroundTabs();
  initClipboardHandlers();
});

// 1. Cursor Spotlight on Ambient Grid
function initCursorSpotlight() {
  window.addEventListener("pointermove", (e) => {
    document.documentElement.style.setProperty("--mouse-x", `${e.clientX}px`);
    document.documentElement.style.setProperty("--mouse-y", `${e.clientY}px`);
  });
}

// 2. Swarm Cockpit Scenarios
function initSwarmCockpit() {
  const presetBtns = document.querySelectorAll(".preset-btn");
  const telemetryEl = document.getElementById("cockpit-telemetry-log");
  const nodes = document.querySelectorAll(".swarm-node-item");

  if (!presetBtns.length || !telemetryEl) return;

  const scenarios = {
    spreadsheets: {
      activeNodes: [0, 1, 3], // Planner, Actor Alpha, Verifier
      logLines: [
        { prefix: "[0.00s]", text: "Intent: 'Automate Q3 financial audit & compute exact SHA-256'", highlight: true },
        { prefix: "[0.02s]", text: "PlannerNode -> Decomposed into 3 causally dependent subtasks." },
        { prefix: "[0.05s]", text: "ActorAlpha provisioned in isolated worktree: .autogenos/worktrees/agent-alpha" },
        { prefix: "[0.12s]", text: "Gated Tools: [os_exec_shell, verifier_assert_hash] (only 2 active tools in context)" },
        { prefix: "[0.28s]", text: "Generated Code-as-Policy synthesized and executed in isolated sandbox." },
        { prefix: "[0.34s]", text: "VerifierNode ground truth check: File exists, SHA-256 e3b0c442 matching expected." },
        { prefix: "[0.36s]", text: "CarryOn: Compacted operational branch -> Retired 3,850 intermediate tokens.", success: true },
        { prefix: "[0.38s]", text: "Status: COMMITTED to durable PostgreSQL checkpointer. Invariants verified.", success: true }
      ]
    },
    windows_ui: {
      activeNodes: [0, 1, 3],
      logLines: [
        { prefix: "[0.00s]", text: "Intent: 'Inspect Windows top-level elements and simulate coordinate click'", highlight: true },
        { prefix: "[0.02s]", text: "OSController -> Native Win32 / UI Automation Tree initialized on host." },
        { prefix: "[0.06s]", text: "Enumerated 42 visible windows. Target 'Calculator' focused via SetForegroundWindow." },
        { prefix: "[0.11s]", text: "EchoPath IBTR Target-Reaiming: Pixel correlation gamma = 0.96 (Direct click at 480, 320)." },
        { prefix: "[0.15s]", text: "Keystroke injected via unicode keybd_event. Zero OCR latency." },
        { prefix: "[0.18s]", text: "VerifierNode: State transition validated. Subtask COMPLETED.", success: true }
      ]
    },
    failure_repair: {
      activeNodes: [0, 2, 3],
      logLines: [
        { prefix: "[0.00s]", text: "Intent: 'Execute untrusted npm package script in isolated sandbox'", highlight: true },
        { prefix: "[0.04s]", text: "ActorBeta provisioned inside ephemeral Firecracker MicroVM (150ms snapshot)." },
        { prefix: "[0.22s]", text: "Execution failed: Non-zero exit code 127 (Command 'pkg-audit' not found)." },
        { prefix: "[0.25s]", text: "VerifierNode: Evidence REJECTED. StructAgent halts hallucinated task progress.", error: true },
        { prefix: "[0.28s]", text: "Dynamic Failure Attribution -> Routed causal discrepancy back to Planner." },
        { prefix: "[0.35s]", text: "Planner synthesized fallback dependency installation policy." },
        { prefix: "[0.48s]", text: "Retry executed -> Exit code 0 -> State COMMITTED successfully.", success: true }
      ]
    }
  };

  function playScenario(key) {
    const sc = scenarios[key];
    if (!sc) return;

    // Update node active states
    nodes.forEach((node, idx) => {
      if (sc.activeNodes.includes(idx)) {
        node.classList.add("active");
      } else {
        node.classList.remove("active");
      }
    });

    // Stream telemetry lines
    telemetryEl.innerHTML = "";
    sc.logLines.forEach((item, idx) => {
      setTimeout(() => {
        const div = document.createElement("div");
        div.className = "log-entry";
        let colorClass = "";
        if (item.highlight) colorClass = "log-highlight";
        if (item.success) colorClass = "log-success";
        if (item.error) colorClass = "style='color:#f43f5e'";

        div.innerHTML = `<span class="log-prefix">${item.prefix}</span> <span class="${colorClass}">${item.text}</span>`;
        telemetryEl.appendChild(div);
        telemetryEl.scrollTop = telemetryEl.scrollHeight;
      }, idx * 120);
    });
  }

  presetBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      presetBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const preset = btn.getAttribute("data-preset");
      playScenario(preset);
    });
  });

  // Play default
  playScenario("spreadsheets");
}

// 3. Tool Attention Benchmarker
function initToolAttentionBenchmarker() {
  const sliderN = document.getElementById("bm-slider-tools");
  const sliderK = document.getElementById("bm-slider-k");
  const valN = document.getElementById("bm-val-tools");
  const valK = document.getElementById("bm-val-k");
  const naiveTokens = document.getElementById("bm-naive-tokens");
  const dynamicTokens = document.getElementById("bm-dynamic-tokens");
  const tokensSaved = document.getElementById("bm-tokens-saved");
  const pctSaved = document.getElementById("bm-pct-saved");

  if (!sliderN || !sliderK) return;

  function recalculate() {
    const N = parseInt(sliderN.value, 10);
    const k = Math.min(parseInt(sliderK.value, 10), N);

    valN.textContent = N;
    valK.textContent = k;

    const naive = N * 450;
    const dynamic = (N * 35) + (k * 450);
    const saved = Math.max(0, naive - dynamic);
    const pct = ((saved / Math.max(1, naive)) * 100).toFixed(1);

    naiveTokens.textContent = naive.toLocaleString() + " tokens";
    dynamicTokens.textContent = dynamic.toLocaleString() + " tokens";
    tokensSaved.textContent = saved.toLocaleString() + " tokens";
    pctSaved.textContent = `${pct}% Context Preserved`;
  }

  sliderN.addEventListener("input", recalculate);
  sliderK.addEventListener("input", recalculate);
  recalculate();
}

// 4. Studio Oscilloscope Audio Visualizer
function initStudioOscilloscope() {
  const canvas = document.getElementById("oscilloscope-canvas");
  const btnSpeak = document.getElementById("btn-voice-stream");
  const btnInterrupt = document.getElementById("btn-voice-interrupt");
  const readoutEl = document.getElementById("voice-readout-status");

  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let state = "standby"; // standby, speech, interrupted
  let phase = 0;

  function renderWave() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw subtle oscilloscope grid lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
    ctx.lineWidth = 1;
    const midY = canvas.height / 2;
    ctx.beginPath();
    ctx.moveTo(0, midY);
    ctx.lineTo(canvas.width, midY);
    ctx.stroke();

    // Waveform trace
    ctx.lineWidth = 2;
    ctx.beginPath();

    if (state === "speech") {
      ctx.strokeStyle = "#06b6d4";
      ctx.shadowColor = "rgba(6, 182, 212, 0.6)";
      ctx.shadowBlur = 8;
      for (let x = 0; x < canvas.width; x += 2) {
        const envelope = Math.sin((x / canvas.width) * Math.PI);
        const y = midY + Math.sin(x * 0.08 + phase) * 35 * envelope * Math.cos(x * 0.03);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
    } else if (state === "interrupted") {
      ctx.strokeStyle = "#f43f5e";
      ctx.shadowColor = "rgba(244, 63, 94, 0.8)";
      ctx.shadowBlur = 10;
      for (let x = 0; x < canvas.width; x += 2) {
        const y = midY + (Math.random() - 0.5) * 8;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
    } else {
      // Standby smooth hum
      ctx.strokeStyle = "#3b82f6";
      ctx.shadowColor = "rgba(59, 130, 246, 0.3)";
      ctx.shadowBlur = 4;
      for (let x = 0; x < canvas.width; x += 3) {
        const y = midY + Math.sin(x * 0.03 + phase * 0.4) * 3;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
    }

    ctx.stroke();
    ctx.shadowBlur = 0; // reset
    phase += 0.12;

    requestAnimationFrame(renderWave);
  }

  renderWave();

  if (btnSpeak) {
    btnSpeak.addEventListener("click", () => {
      state = "speech";
      if (readoutEl) readoutEl.innerHTML = "<span style='color:#06b6d4'>Streaming Audio: Silero VAD 0.22ms • TTFA 312ms • Turn Active</span>";
      setTimeout(() => {
        if (state === "speech") {
          state = "standby";
          if (readoutEl) readoutEl.innerHTML = "<span style='color:#10b981'>Turn Complete. Listening on local WebRTC channel (ws://127.0.0.1:7880)...</span>";
        }
      }, 5000);
    });
  }

  if (btnInterrupt) {
    btnInterrupt.addEventListener("click", () => {
      state = "interrupted";
      if (readoutEl) readoutEl.innerHTML = "<span style='color:#f43f5e'>Barge-in Interrupt: VAD Triggered • Discarded 8 audio frames in <1ms</span>";
      setTimeout(() => {
        state = "standby";
        if (readoutEl) readoutEl.innerHTML = "<span style='color:#94a3b8'>Standby: Microphone active.</span>";
      }, 2200);
    });
  }
}

// 5. Code Playground Tab Switcher
function initPlaygroundTabs() {
  const tabs = document.querySelectorAll(".playground-tab");
  const codeBlock = document.getElementById("pg-code");
  if (!tabs.length || !codeBlock) return;

  const codeSnippets = {
    python: `import asyncio
import autogenos as agy

async def main():
    # 1. Initialize Swarm Orchestrator with Planner-Actor-Verifier lifecycle
    orchestrator = agy.SwarmOrchestrator()

    # 2. Gate tools dynamically via Tool Attention (eliminates MCP token tax)
    engine = agy.ToolAttentionEngine()
    active_tools = engine.gate_tools("Process financial invoice and compute file hash", top_k=2)

    # 3. Execute closed-loop long-horizon task with causal verification
    controller = agy.SwarmGraphController()
    state = await controller.run_full_lifecycle(
        "Audit spreadsheet records and verify checksum with zero side effects"
    )

    print(f"Task Phase:      {state.phase.value}")
    print(f"Verified Proofs: {len(state.accumulated_evidence)}")
    print(f"Tokens Pruned:   {state.token_usage_pruned} tokens via CarryOn")

if __name__ == "__main__":
    asyncio.run(main())`,

    cli: `# 1. Dispatch an autonomous task to the Planner-Actor-Verifier swarm
autogenos run "Open Notepad, write system metrics, and verify window"

# 2. Inspect dynamic Tool Attention semantic gating & MCP token savings
autogenos tool-attention "Inspect desktop UI elements and click button" --top-k 2

# 3. Launch 100% free local LiveKit WebRTC room
autogenos livekit-local

# 4. Speak text locally via zero-cost offline SAPI5 TTS
autogenos speak "AutogenOS autonomous multi-agent swarm operational."

# 5. Launch high-performance REST and WebSocket API server
autogenos serve --port 8000`,

    rest: `POST /api/v1/orchestrator/run HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "intent": "Perform atomic cross-stack database migration and verify test pass",
  "max_steps": 10
}

# Response (200 OK):
{
  "session_id": "8f3e12-c42",
  "phase": "COMPLETED",
  "subtasks_total": 3,
  "evidence_passed": 3,
  "tokens_pruned": 4050
}`,

    websocket: `// Connect to sub-500ms Real-Time Voice WebSocket
const ws = new WebSocket("ws://127.0.0.1:8000/api/v1/voice/stream");

ws.onopen = () => {
  ws.send(JSON.stringify({ prompt: "Report status of active Git worktrees" }));
};

ws.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  console.log("Token:", chunk.token, "| Latency:", chunk.latency_ms + "ms");
};`
  };

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const key = tab.getAttribute("data-tab");
      if (codeSnippets[key]) {
        codeBlock.textContent = codeSnippets[key];
      }
    });
  });
}

// 6. Clipboard Copy Handlers
function initClipboardHandlers() {
  const copyBtn = document.getElementById("btn-copy-install");
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText("pip install autogenos");
      copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
      setTimeout(() => {
        copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
      }, 2000);
    });
  }
}
