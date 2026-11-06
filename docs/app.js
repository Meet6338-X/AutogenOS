// AutogenOS Interactive JavaScript Engine

document.addEventListener("DOMContentLoaded", () => {
  initParticleCanvas();
  initTerminalSimulator();
  initToolAttentionCalculator();
  initAudioWaveformSimulator();
  initCodePlaygroundTabs();
});

// 1. Particle Canvas Background
function initParticleCanvas() {
  const canvas = document.getElementById("particle-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  const particleCount = Math.min(width > 768 ? 60 : 25, 80);

  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.45,
      vy: (Math.random() - 0.5) * 0.45,
      radius: Math.random() * 1.8 + 0.8,
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    // Draw connecting lines
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 130) {
          ctx.strokeStyle = `rgba(59, 130, 246, ${0.12 * (1 - dist / 130)})`;
          ctx.lineWidth = 0.8;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }

    // Draw and update particles
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0 || p.x > width) p.vx *= -1;
      if (p.y < 0 || p.y > height) p.vy *= -1;

      ctx.fillStyle = "rgba(6, 182, 212, 0.65)";
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fill();
    }

    requestAnimationFrame(render);
  }

  render();
}

// 2. Interactive Terminal Simulator
function initTerminalSimulator() {
  const terminalBody = document.getElementById("terminal-typing-area");
  if (!terminalBody) return;

  const scenarios = [
    {
      cmd: "autogenos run \"Process invoices and verify spreadsheet hash\"",
      output: [
        "[+] Initializing Swarm Orchestrator (Session: 9a4f21-b)...",
        "[PlannerNode] Intent decomposed into 3 atomic causal subtasks.",
        "[ActorNode] Subtask 1 provisioned in isolated worktree: .autogenos/worktrees/actor-alpha",
        "[VerifierNode] Exit code 0, SHA-256 hash e3b0c442 attached -> State COMMITTED.",
        "[CarryOn] Compacted operational history -> Pruned 3,850 tokens (86% memory saved).",
        "Result: COMPLETED (3 subtasks, 3 verified evidence items, 0 errors)"
      ]
    },
    {
      cmd: "autogenos tool-attention \"Click button on Windows desktop and inspect element\"",
      output: [
        "[ToolAttention] Cosine similarity gating active over 8 tools...",
        "Promoted (2 tools): os_send_input, os_inspect_element",
        "Naive MCP Tax:    ~3,600 tokens",
        "Tool Attention:   ~1,180 tokens (67.2% tokens saved)",
        "Headroom Gain:    +67.2% KV-cache preserved."
      ]
    },
    {
      cmd: "autogenos voice",
      output: [
        "[+] Sub-500ms Real-Time Voice Pipeline Initialized:",
        "    * Silero VAD Latency:        0.22 ms",
        "    * TurnDetector v1-mini:      1.3 ms (ALiBi Transformer)",
        "    * Dynamic EMA Endpointing:   Initial delay 0.80s (alpha=0.9)",
        "    * TTFA Target Met:           312.4 ms (<500ms threshold)"
      ]
    }
  ];

  let scenarioIdx = 0;

  function typeScenario() {
    const sc = scenarios[scenarioIdx];
    terminalBody.innerHTML = `<span class="prompt-prefix">user@autogenos:~$</span><span id="typed-cmd"></span><span class="cursor-blink"></span><div id="output-area" class="term-output"></div>`;

    const typedCmdEl = document.getElementById("typed-cmd");
    const outputAreaEl = document.getElementById("output-area");
    let charIdx = 0;

    const interval = setInterval(() => {
      typedCmdEl.textContent += sc.cmd[charIdx];
      charIdx++;
      if (charIdx >= sc.cmd.length) {
        clearInterval(interval);
        setTimeout(() => {
          outputAreaEl.innerHTML = sc.output.map(line => `<div>${line}</div>`).join("");
          scenarioIdx = (scenarioIdx + 1) % scenarios.length;
          setTimeout(typeScenario, 4000);
        }, 500);
      }
    }, 40);
  }

  typeScenario();
}

// 3. Tool Attention vs MCP Tax Calculator
function initToolAttentionCalculator() {
  const toolsSlider = document.getElementById("slider-tool-count");
  const topKSlider = document.getElementById("slider-top-k");
  const toolCountVal = document.getElementById("val-tool-count");
  const topKVal = document.getElementById("val-top-k");
  const naiveTokensEl = document.getElementById("calc-naive-tokens");
  const dynamicTokensEl = document.getElementById("calc-dynamic-tokens");
  const tokensSavedEl = document.getElementById("calc-tokens-saved");
  const pctSavedEl = document.getElementById("calc-pct-saved");
  const fillBar = document.getElementById("calc-fill-bar");

  if (!toolsSlider || !topKSlider) return;

  function update() {
    const N = parseInt(toolsSlider.value, 10);
    const k = Math.min(parseInt(topKSlider.value, 10), N);

    toolCountVal.textContent = N;
    topKVal.textContent = k;

    const naive = N * 450;
    const dynamic = (N * 35) + (k * 450);
    const saved = Math.max(0, naive - dynamic);
    const pct = ((saved / Math.max(1, naive)) * 100).toFixed(1);

    naiveTokensEl.textContent = naive.toLocaleString() + " tokens";
    dynamicTokensEl.textContent = dynamic.toLocaleString() + " tokens";
    tokensSavedEl.textContent = saved.toLocaleString() + " tokens";
    pctSavedEl.textContent = pct + "% saved";
    fillBar.style.width = pct + "%";
  }

  toolsSlider.addEventListener("input", update);
  topKSlider.addEventListener("input", update);
  update();
}

// 4. Live Audio Waveform Simulator
function initAudioWaveformSimulator() {
  const canvas = document.getElementById("waveform-canvas");
  const btnSpeak = document.getElementById("btn-sim-speak");
  const btnBargeIn = document.getElementById("btn-sim-bargein");
  const statusEl = document.getElementById("voice-status-text");

  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let mode = "idle"; // idle, speaking, bargein
  let step = 0;

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.lineWidth = 2.5;
    ctx.beginPath();

    const mid = canvas.height / 2;
    for (let x = 0; x < canvas.width; x += 3) {
      let amp = 5;
      if (mode === "speaking") {
        amp = 30 * Math.sin(x * 0.05 + step * 0.1) * Math.cos(x * 0.02);
        ctx.strokeStyle = "#06b6d4";
      } else if (mode === "bargein") {
        amp = 45 * (Math.random() - 0.5);
        ctx.strokeStyle = "#f43f5e";
      } else {
        amp = 3 * Math.sin(x * 0.02 + step * 0.02);
        ctx.strokeStyle = "#3b82f6";
      }

      const y = mid + amp;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }

    ctx.stroke();
    step++;
    requestAnimationFrame(draw);
  }

  draw();

  if (btnSpeak) {
    btnSpeak.addEventListener("click", () => {
      mode = "speaking";
      if (statusEl) statusEl.innerHTML = `<span style="color:#06b6d4">Agent Streaming Turn: TTFA ~320ms | Overlapped STT & TTS</span>`;
      setTimeout(() => {
        if (mode === "speaking") {
          mode = "idle";
          if (statusEl) statusEl.innerHTML = `<span style="color:#10b981">Turn Completed Deterministically. Listening for input...</span>`;
        }
      }, 4500);
    });
  }

  if (btnBargeIn) {
    btnBargeIn.addEventListener("click", () => {
      mode = "bargein";
      if (statusEl) statusEl.innerHTML = `<span style="color:#f43f5e">⚡ Barge-in Interruption Detected! Audio Queue Flushed in <1ms.</span>`;
      setTimeout(() => {
        mode = "idle";
        if (statusEl) statusEl.innerHTML = `<span style="color:#94a3b8">Ready for next user turn.</span>`;
      }, 2000);
    });
  }
}

// 5. Code Playground Tab Switcher
function initCodePlaygroundTabs() {
  const tabs = document.querySelectorAll(".code-tab");
  const codeBlock = document.getElementById("playground-code-block");
  if (!tabs.length || !codeBlock) return;

  const snippets = {
    python: `import asyncio
import autogenos as agy

async def main():
    # 1. Initialize Swarm Orchestrator
    controller = agy.SwarmGraphController()

    # 2. Execute long-horizon objective with causal verification
    state = await controller.run_full_lifecycle(
        "Automate financial spreadsheet audit and verify SHA-256"
    )

    print(f"Task Phase:      {state.phase.value}")
    print(f"Evidence Passed: {len(state.accumulated_evidence)}")
    print(f"Tokens Pruned:   {state.token_usage_pruned} (via CarryOn)")

if __name__ == "__main__":
    asyncio.run(main())`,

    cli: `# 1. Dispatch an autonomous task through the Planner-Actor-Verifier loop
autogenos run "Open Notepad and type system diagnostic info"

# 2. Inspect dynamic Tool Attention semantic gating & MCP token savings
autogenos tool-attention "Inspect desktop elements and click submit" --top-k 2

# 3. Start 100% free local LiveKit WebRTC audio room
autogenos livekit-local

# 4. Speak text locally via zero-cost native TTS
autogenos speak "AutogenOS autonomous multi-agent swarm operational."

# 5. Launch high-performance REST and WebSocket API server
autogenos serve --port 8000`,

    api: `POST /api/v1/orchestrator/run HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "intent": "Perform atomic cross-stack mutation and verify test pass",
  "max_steps": 10
}

# Response:
{
  "session_id": "9a4f21-b38",
  "phase": "COMPLETED",
  "subtasks_total": 3,
  "evidence_passed": 3,
  "tokens_pruned": 4050
}`,

    websocket: `// Connect to sub-500ms Real-Time Voice WebSocket
const ws = new WebSocket("ws://127.0.0.1:8000/api/v1/voice/stream");

ws.onopen = () => {
  ws.send(JSON.stringify({ prompt: "Status update on active worktrees" }));
};

ws.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  console.log("Streamed Token:", chunk.token, "Latency:", chunk.latency_ms + "ms");
};`
  };

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const key = tab.getAttribute("data-tab");
      if (snippets[key]) {
        codeBlock.textContent = snippets[key];
      }
    });
  });
}
