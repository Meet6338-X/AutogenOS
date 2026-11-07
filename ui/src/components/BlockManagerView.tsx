'use client';

import React, { useState, useEffect } from 'react';
import {
  Boxes,
  Plus,
  Play,
  ToggleLeft,
  ToggleRight,
  Code2,
  Search,
  Terminal,
} from 'lucide-react';
import { BlockItem } from '../lib/types';
import { api } from '../lib/api';
import { soundFX } from '../lib/sound';

export default function BlockManagerView() {
  const [blocks, setBlocks] = useState<BlockItem[]>([]);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedBlock, setSelectedBlock] = useState<BlockItem | null>(null);
  const [execParams, setExecParams] = useState<string>('{\n  "query": "autogenos",\n  "max_results": 3\n}');
  const [execResult, setExecResult] = useState<any>(null);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);

  // New Block Form Modal
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [newBlockId, setNewBlockId] = useState<string>('tool.custom_metric');
  const [newBlockType, setNewBlockType] = useState<string>('TOOL');
  const [newBlockCode, setNewBlockCode] = useState<string>(
    `def execute(*args, **kwargs):\n    """Custom dynamic modular block."""\n    return {"status": "ok", "processed": kwargs}\n`
  );

  useEffect(() => {
    loadBlocks();
  }, []);

  const loadBlocks = async () => {
    try {
      const data = await api.fetchBlocks();
      setBlocks(data);
    } catch (e) {
      console.warn('Failed to fetch blocks:', e);
    }
  };

  const handleToggle = async (block: BlockItem) => {
    const nextState = !block.enabled;
    soundFX.playActionTone();
    // Optimistic UI update
    setBlocks((prev) =>
      prev.map((b) => (b.id === block.id ? { ...b, enabled: nextState } : b))
    );
    await api.toggleBlock(block.id, nextState);
  };

  const handleExecute = async () => {
    if (!selectedBlock) return;
    setIsExecuting(true);
    soundFX.playActionTone();
    try {
      let parsed = {};
      try {
        parsed = JSON.parse(execParams);
      } catch {
        parsed = { raw: execParams };
      }
      const res = await api.executeBlock(selectedBlock.id, parsed);
      setExecResult(res);
      soundFX.playSuccessChime();
    } catch (err: any) {
      setExecResult({ error: err?.message || 'Execution failed' });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleRegisterBlock = async () => {
    if (!newBlockCode) return;
    try {
      const b = await api.registerBlock(newBlockCode, newBlockId, newBlockType);
      setBlocks((prev) => [b, ...prev]);
      setShowAddModal(false);
      soundFX.playSuccessChime();
      api.speakText(`Modular block ${b.id} registered and loaded.`);
    } catch (err: any) {
      alert(`Registration failed: ${err?.message}`);
    }
  };

  const filteredBlocks = blocks.filter((b) => {
    const matchesFilter = filterType === 'ALL' || b.type.toUpperCase() === filterType.toUpperCase();
    const matchesSearch =
      b.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      b.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      b.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getBadgeColor = (type: string) => {
    switch (type.toUpperCase()) {
      case 'TOOL':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'PERCEPTION':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'ACTION':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'POLICY':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'EVAL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-700/30 text-slate-300 border-slate-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-3xl border border-cyan-500/20 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 flex items-center justify-center text-cyan-400 border border-cyan-500/30">
              <Boxes className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Modular Block Runtime
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                  Hot-Pluggable Components
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Easily register, enable, disable, and execute isolated capabilities across tools, perception, and policies.
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            Register New Block
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1">
          {['ALL', 'TOOL', 'ACTION', 'PERCEPTION', 'POLICY', 'EVAL'].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold font-mono transition-all ${
                filterType === type
                  ? 'bg-cyan-500 text-black shadow-md shadow-cyan-500/30'
                  : 'bg-slate-900/60 hover:bg-slate-800 text-slate-400 border border-slate-800'
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search blocks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full glass-input pl-9 pr-3 py-2 rounded-xl text-xs font-mono"
          />
        </div>
      </div>

      {/* Blocks Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredBlocks.map((block) => (
          <div
            key={block.id}
            className={`glass-panel p-5 rounded-3xl border transition-all flex flex-col justify-between gap-4 ${
              block.enabled
                ? 'border-slate-800/80 hover:border-cyan-500/40'
                : 'border-slate-900/60 opacity-60'
            }`}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-md border ${getBadgeColor(block.type)}`}>
                  {block.type}
                </span>

                <button
                  onClick={() => handleToggle(block)}
                  title={block.enabled ? 'Click to disable' : 'Click to enable'}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  {block.enabled ? (
                    <ToggleRight className="w-6 h-6 text-emerald-400" />
                  ) : (
                    <ToggleLeft className="w-6 h-6 text-slate-600" />
                  )}
                </button>
              </div>

              <div>
                <h4 className="font-bold text-slate-100 text-sm flex items-center gap-1.5">
                  {block.name}
                </h4>
                <div className="text-[11px] font-mono text-cyan-400/80 mt-0.5">{block.id}</div>
              </div>

              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                {block.description}
              </p>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-800/60 text-xs">
              <span className="text-[10px] font-mono text-slate-500">
                Runs: {block.execution_count ?? 0}
              </span>

              <button
                onClick={() => {
                  setSelectedBlock(block);
                  setExecResult(null);
                }}
                disabled={!block.enabled}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-xl font-mono text-xs font-semibold transition-all ${
                  block.enabled
                    ? 'bg-slate-800 hover:bg-cyan-500 hover:text-black text-cyan-300'
                    : 'bg-slate-900 text-slate-600 cursor-not-allowed'
                }`}
              >
                <Play className="w-3.5 h-3.5" />
                Execute
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Execute Modal */}
      {selectedBlock && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-xl glass-panel-glow rounded-3xl p-6 border border-cyan-500/30 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Play className="w-4 h-4 text-cyan-400" />
                  Execute Modular Block
                </h3>
                <div className="text-xs font-mono text-cyan-300">{selectedBlock.id}</div>
              </div>
              <button
                onClick={() => setSelectedBlock(null)}
                className="text-slate-400 hover:text-white text-xs font-mono p-1"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Execution Parameters (JSON kwargs)</label>
              <textarea
                rows={5}
                value={execParams}
                onChange={(e) => setExecParams(e.target.value)}
                className="w-full glass-input p-3 rounded-2xl font-mono text-xs text-cyan-200"
              />
            </div>

            <button
              onClick={handleExecute}
              disabled={isExecuting}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg"
            >
              {isExecuting ? <Terminal className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              Run Block Execution
            </button>

            {execResult && (
              <div className="space-y-1">
                <div className="text-[10px] font-mono text-slate-400">Result Output:</div>
                <pre className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-emerald-300 overflow-x-auto max-h-48">
                  {JSON.stringify(execResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add Block Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-2xl glass-panel-glow rounded-3xl p-6 border border-cyan-500/30 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Code2 className="w-4 h-4 text-cyan-400" />
                Register Dynamic Block
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white text-xs font-mono p-1"
              >
                ✕ Cancel
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Block Identifier</label>
                <input
                  type="text"
                  value={newBlockId}
                  onChange={(e) => setNewBlockId(e.target.value)}
                  className="w-full glass-input px-3 py-2 rounded-xl text-xs font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Block Type</label>
                <select
                  value={newBlockType}
                  onChange={(e) => setNewBlockType(e.target.value)}
                  className="w-full glass-input px-3 py-2 rounded-xl text-xs bg-slate-900"
                >
                  <option value="TOOL">TOOL</option>
                  <option value="ACTION">ACTION</option>
                  <option value="PERCEPTION">PERCEPTION</option>
                  <option value="POLICY">POLICY</option>
                  <option value="EVAL">EVAL</option>
                  <option value="CUSTOM">CUSTOM</option>
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Python Implementation Code</label>
              <textarea
                rows={8}
                value={newBlockCode}
                onChange={(e) => setNewBlockCode(e.target.value)}
                className="w-full glass-input p-3 rounded-2xl font-mono text-xs text-cyan-300"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleRegisterBlock}
                className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs shadow-lg shadow-cyan-500/30"
              >
                Compile & Register
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
