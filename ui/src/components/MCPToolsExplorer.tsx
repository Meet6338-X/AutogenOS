'use client';

import React, { useState, useEffect } from 'react';
import {
  Wrench,
  Search,
  Code,
  Play,
  Terminal,
  CheckCircle2,
} from 'lucide-react';
import { MCPToolItem } from '../lib/types';
import { api } from '../lib/api';
import { soundFX } from '../lib/sound';

export default function MCPToolsExplorer() {
  const [tools, setTools] = useState<MCPToolItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTool, setSelectedTool] = useState<MCPToolItem | null>(null);
  const [paramsInput, setParamsInput] = useState('{}');
  const [output, setOutput] = useState<any>(null);
  const [isCalling, setIsCalling] = useState(false);

  const loadTools = async () => {
    try {
      const data = await api.fetchMCPTools();
      setTools(data);
    } catch (e) {
      console.warn('Failed to fetch MCP tools:', e);
    }
  };

  useEffect(() => {
    loadTools();
  }, []);

  const handleSelectTool = (tool: MCPToolItem) => {
    setSelectedTool(tool);
    setOutput(null);
    const defaultArgs: Record<string, any> = {};
    if (tool.input_schema?.properties) {
      for (const [key, prop] of Object.entries(tool.input_schema.properties)) {
        defaultArgs[key] = prop.type === 'number' ? 0 : 'sample_value';
      }
    }
    setParamsInput(JSON.stringify(defaultArgs, null, 2));
  };

  const handleCallTool = async () => {
    if (!selectedTool) return;
    setIsCalling(true);
    soundFX.playActionTone();
    try {
      let args = {};
      try {
        args = JSON.parse(paramsInput);
      } catch {
        args = { raw: paramsInput };
      }
      // Using executeBlock or MCP call
      const res = await api.executeBlock(selectedTool.name, args);
      setOutput(res);
      soundFX.playSuccessChime();
    } catch (err: any) {
      setOutput({ error: err?.message || 'Call failed' });
    } finally {
      setIsCalling(false);
    }
  };

  const filteredTools = tools.filter(
    (t) =>
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-3xl border border-cyan-500/20 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 flex items-center justify-center text-cyan-400 border border-cyan-500/30">
              <Wrench className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                MCP Tools & Schema Explorer
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                  Model Context Protocol 2.0
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Standardized JSON-RPC 2.0 agent tools with automatic Tool Attention context sparsification.
              </p>
            </div>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full glass-input pl-9 pr-3 py-2 rounded-xl text-xs font-mono"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tools List */}
        <div className="space-y-3">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
            Registered Tools ({filteredTools.length})
          </div>
          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {filteredTools.map((t) => (
              <div
                key={t.name}
                onClick={() => handleSelectTool(t)}
                className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                  selectedTool?.name === t.name
                    ? 'bg-cyan-500/15 border-cyan-500/50 shadow-lg shadow-cyan-500/10'
                    : 'bg-slate-900/40 border-slate-800 hover:bg-slate-800/60'
                }`}
              >
                <div className="font-mono font-bold text-xs text-cyan-300">{t.name}</div>
                <div className="text-xs text-slate-400 line-clamp-2 mt-1 leading-relaxed">
                  {t.description}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Tool Details & Interactive Runner */}
        <div className="lg:col-span-2 space-y-4">
          {selectedTool ? (
            <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-5">
              <div>
                <div className="text-xs font-mono text-cyan-400 uppercase">Selected Tool</div>
                <h3 className="text-lg font-bold text-white font-mono mt-0.5">{selectedTool.name}</h3>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  {selectedTool.description}
                </p>
              </div>

              {/* JSON Schema */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                  <Code className="w-3.5 h-3.5 text-cyan-400" />
                  Input JSON Schema
                </label>
                <pre className="p-3 rounded-2xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto">
                  {JSON.stringify(selectedTool.input_schema, null, 2)}
                </pre>
              </div>

              {/* Arguments Input */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5 text-purple-400" />
                  Tool Invocation Arguments (JSON)
                </label>
                <textarea
                  rows={4}
                  value={paramsInput}
                  onChange={(e) => setParamsInput(e.target.value)}
                  className="w-full glass-input p-3 rounded-2xl font-mono text-xs text-cyan-300"
                />
              </div>

              {/* Run Tool Button */}
              <button
                onClick={handleCallTool}
                disabled={isCalling}
                className="w-full py-3 rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20 transition-all active:scale-95"
              >
                {isCalling ? <Terminal className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Call MCP Tool Now
              </button>

              {/* Invocation Output */}
              {output && (
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <div className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 font-mono">
                    <CheckCircle2 className="w-4 h-4" /> Execution Result
                  </div>
                  <pre className="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-xs font-mono text-emerald-300 overflow-x-auto max-h-56">
                    {JSON.stringify(output, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel p-12 rounded-3xl border border-slate-800 text-center text-slate-500 font-mono text-xs flex flex-col items-center justify-center gap-3">
              <Wrench className="w-8 h-8 text-slate-600" />
              Select an MCP tool from the left to inspect its schema and run test calls.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
