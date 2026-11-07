'use client';

import React, { useState } from 'react';
import {
  Zap,
  Video,
  Boxes,
  Activity,
  Wrench,
} from 'lucide-react';
import SwarmCockpit from '../components/SwarmCockpit';
import MeetingController from '../components/MeetingController';
import BlockManagerView from '../components/BlockManagerView';
import DoctorDashboard from '../components/DoctorDashboard';
import MCPToolsExplorer from '../components/MCPToolsExplorer';
import LiveKitVoiceHUD from '../components/LiveKitVoiceHUD';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'swarm' | 'meetings' | 'blocks' | 'doctor' | 'mcp'>('swarm');
  const [activeGoal, setActiveGoal] = useState<string>('');
  const [activeMeetUrl, setActiveMeetUrl] = useState<string>('https://meet.google.com/hsw-hmdc-gqc');

  const tabs = [
    { id: 'swarm', label: 'Swarm Cockpit', icon: Zap },
    { id: 'meetings', label: 'Meeting Agent', icon: Video },
    { id: 'blocks', label: 'Modular Blocks', icon: Boxes },
    { id: 'doctor', label: 'System Doctor', icon: Activity },
    { id: 'mcp', label: 'MCP Tools', icon: Wrench },
  ];

  return (
    <div className="min-h-screen bg-[#06080e] text-slate-100 flex flex-col relative">
      {/* Background Cyber Grid Accent */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-25 pointer-events-none" />

      {/* Top Cockpit Navigation Bar */}
      <header className="sticky top-0 z-40 glass-panel border-b border-slate-800/80 px-4 sm:px-8 py-3.5 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="relative w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white font-black text-sm tracking-tighter">
              <span className="relative z-10">AO</span>
              <div className="absolute inset-0 rounded-xl bg-cyan-400 blur-sm opacity-40 animate-pulse" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base tracking-tight text-white">
                  AutogenOS
                </span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  v0.1.0 Sovereign
                </span>
              </div>
              <div className="text-[10px] text-slate-400 font-mono hidden sm:block">
                Recursive Self-Improving Multi-Agent OS & Voice Cockpit
              </div>
            </div>
          </div>

          {/* Tab Switcher Pills */}
          <nav className="flex items-center gap-1 bg-slate-950/70 p-1 rounded-2xl border border-slate-800/80 overflow-x-auto max-w-[55vw] sm:max-w-none">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl text-xs font-semibold font-mono transition-all duration-150 whitespace-nowrap ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/20'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span className="hidden md:inline">{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* System Telemetry & Latency Pill */}
          <div className="flex items-center gap-2.5">
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-400">System:</span>
              <span className="text-emerald-400 font-bold">OPERATIONAL</span>
              <span className="text-slate-600">|</span>
              <span className="text-cyan-400">&lt;10ms</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Cockpit Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-8 space-y-8 relative z-10">
        {activeTab === 'swarm' && (
          <SwarmCockpit
            initialGoal={activeGoal}
            key={activeGoal || 'swarm'}
          />
        )}

        {activeTab === 'meetings' && (
          <MeetingController
            initialUrl={activeMeetUrl}
            key={activeMeetUrl || 'meetings'}
          />
        )}

        {activeTab === 'blocks' && <BlockManagerView />}

        {activeTab === 'doctor' && <DoctorDashboard />}

        {activeTab === 'mcp' && <MCPToolsExplorer />}
      </main>

      {/* Persistent Floating / Pop-out LiveKit Voice HUD */}
      <LiveKitVoiceHUD
        onNavigateTab={(tab) => {
          if (['swarm', 'meetings', 'blocks', 'doctor', 'mcp'].includes(tab)) {
            setActiveTab(tab as any);
          }
        }}
        onExecuteGoal={(goal) => {
          setActiveGoal(goal);
          setActiveTab('swarm');
        }}
        onQuickJoinMeet={(url) => {
          setActiveMeetUrl(url);
          setActiveTab('meetings');
        }}
      />
    </div>
  );
}
