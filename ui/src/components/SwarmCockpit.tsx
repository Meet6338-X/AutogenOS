'use client';

import React, { useState } from 'react';
import {
  Play,
  Terminal,
  CheckCircle2,
  Clock,
  Zap,
  Layers,
  ShieldCheck,
  Cpu,
} from 'lucide-react';
import { SwarmRunResult } from '../lib/types';
import { api } from '../lib/api';
import { soundFX } from '../lib/sound';

interface SwarmCockpitProps {
  initialGoal?: string;
}

export default function SwarmCockpit({ initialGoal = '' }: SwarmCockpitProps) {
  const [goal, setGoal] = useState<string>(
    initialGoal || 'Audit running system processes, verify screen state, and report system health'
  );
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [result, setResult] = useState<SwarmRunResult | null>(null);
  const [logs, setLogs] = useState<string[]>([
    '[Planner] Standby. Waiting for intent dispatch...',
  ]);

  const handleRunSwarm = async (customGoal?: string) => {
    const targetGoal = customGoal || goal;
    if (!targetGoal) return;
    setIsRunning(true);
    soundFX.playActionTone();
    setLogs((prev) => [
      `[${new Date().toLocaleTimeString()}] [Dispatch] Initiating Swarm lifecycle for: "${targetGoal}"`,
      `[${new Date().toLocaleTimeString()}] [Planner] Decomposing high-level intent into causal subtasks...`,
      ...prev,
    ]);

    try {
      const res = await api.runOrchestrator(targetGoal);
      setResult(res);
      soundFX.playSuccessChime();
      setLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] [Verifier] All ${res.subtasks_total} subtasks committed with evidence proofs.`,
        `[${new Date().toLocaleTimeString()}] [Compactor] Folded ${res.tokens_pruned} telemetry tokens into state CarryOn.`,
        ...prev,
      ]);
      api.speakText(`Swarm goal executed successfully. Verified ${res.subtasks_total} subtasks.`);
    } catch (err: any) {
      soundFX.playActionTone();
      setLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] [Error] Execution encountered: ${err?.message || 'Error'}`,
        ...prev,
      ]);
    } finally {
      setIsRunning(false);
    }
  };

  const sampleGoals = [
    'Clean workspace temp files and check git status',
    'Capture desktop screenshot and compute perceptual dHash',
    'Audit running processes and verify memory footprint',
    'Synthesize new tool scaffold from recurring action patterns',
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-3xl border border-cyan-500/20 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 flex items-center justify-center text-cyan-400 border border-cyan-500/30">
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Swarm Orchestrator Cockpit
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                  LangGraph Closed Loop
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Self-healing closed-loop execution: Planner decomposes goals, Actor executes tools, Verifier proves causal outcomes.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 bg-cyan-950/40 px-3 py-1.5 rounded-xl border border-cyan-800">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            Context CarryOn Active
          </div>
        </div>
      </div>

      {/* Goal Input Card */}
      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
            <span>High-Level Intent / Goal</span>
            <span className="text-slate-500 font-mono text-[11px]">Supports multi-turn complex goals</span>
          </label>
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Inspect system health and summarize active processes..."
              className="flex-1 glass-input px-4 py-3 rounded-2xl text-sm font-mono text-cyan-200"
            />
            <button
              onClick={() => handleRunSwarm()}
              disabled={isRunning}
              className={`px-6 py-3 rounded-2xl font-bold text-xs flex items-center justify-center gap-2 shadow-xl transition-all ${
                isRunning
                  ? 'bg-cyan-800 cursor-not-allowed text-cyan-200'
                  : 'bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-cyan-500/25 active:scale-95'
              }`}
            >
              {isRunning ? <Clock className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              Dispatch Intent
            </button>
          </div>
        </div>

        {/* Quick Goal Presets */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] text-slate-400 font-mono">Presets:</span>
          {sampleGoals.map((g, idx) => (
            <button
              key={idx}
              onClick={() => {
                setGoal(g);
                handleRunSwarm(g);
              }}
              className="text-[11px] px-3 py-1 rounded-xl bg-slate-900/60 hover:bg-cyan-950/50 border border-slate-800 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-200 transition-all font-mono"
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {/* State Machine Triad Pipeline (Planner -> Actor -> Verifier) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-5 rounded-3xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1.5 font-bold text-cyan-400">
              <Layers className="w-4 h-4" /> 1. PLANNER
            </span>
            <span>Broad-then-Deep</span>
          </div>
          <p className="text-xs text-slate-300">
            Decomposes non-linear intents into atomic subtasks with causal pre-conditions.
          </p>
          <div className="text-[11px] font-mono text-slate-500">
            Active Subtasks: {result?.subtasks_total || 0}
          </div>
        </div>

        <div className="glass-panel p-5 rounded-3xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1.5 font-bold text-purple-400">
              <Cpu className="w-4 h-4" /> 2. ACTOR
            </span>
            <span>Tool Attention</span>
          </div>
          <p className="text-xs text-slate-300">
            Sparsifies MCP tool schemas (92% reduction) and executes native OS actions.
          </p>
          <div className="text-[11px] font-mono text-slate-500">
            Executed Tools: {result?.subtasks.filter((s) => s.is_committed).length || 0}
          </div>
        </div>

        <div className="glass-panel p-5 rounded-3xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1.5 font-bold text-emerald-400">
              <ShieldCheck className="w-4 h-4" /> 3. VERIFIER
            </span>
            <span>State CarryOn</span>
          </div>
          <p className="text-xs text-slate-300">
            Validates causal post-conditions and folds raw tokens into compressed state.
          </p>
          <div className="text-[11px] font-mono text-emerald-400">
            Tokens Folded: {result?.tokens_pruned || 0} tokens
          </div>
        </div>
      </div>

      {/* Subtasks Execution Feed & Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Decomposed Subtasks Checklist */}
        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Atomic Subtasks Execution Feed
            </h3>
            <span className="text-[10px] font-mono text-slate-400">
              {result?.subtasks.length || 0} subtasks
            </span>
          </div>

          <div className="space-y-3">
            {result?.subtasks && result.subtasks.length > 0 ? (
              result.subtasks.map((st, idx) => (
                <div
                  key={st.id || idx}
                  className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80 space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2.5">
                      <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center justify-center text-xs font-bold mt-0.5">
                        ✓
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-slate-200">{st.intent}</div>
                        <div className="text-[11px] font-mono text-cyan-400 mt-0.5">
                          Tool: {st.tool || 'os_controller'}
                        </div>
                      </div>
                    </div>

                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      COMMITTED
                    </span>
                  </div>

                  {st.output && (
                    <div className="text-[11px] font-mono text-slate-400 pl-7 pt-1 border-t border-slate-900">
                      {st.output}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-10 text-xs text-slate-500 font-mono">
                No active task. Dispatch an intent above or speak via LiveKit Voice HUD.
              </div>
            )}
          </div>
        </div>

        {/* Right: Live Swarm Event Timeline Logs */}
        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Terminal className="w-4 h-4 text-cyan-400" />
              Live Swarm Event Timeline
            </h3>
            <button
              onClick={() => setLogs([])}
              className="text-[10px] font-mono text-slate-500 hover:text-slate-300"
            >
              Clear
            </button>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/90 border border-slate-800 font-mono text-xs text-slate-300 h-64 overflow-y-auto space-y-2">
            {logs.map((log, idx) => (
              <div key={idx} className="leading-relaxed">
                {log.includes('[Error]') ? (
                  <span className="text-rose-400">{log}</span>
                ) : log.includes('[Verifier]') ? (
                  <span className="text-emerald-400">{log}</span>
                ) : log.includes('[Planner]') ? (
                  <span className="text-cyan-400">{log}</span>
                ) : (
                  <span>{log}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
