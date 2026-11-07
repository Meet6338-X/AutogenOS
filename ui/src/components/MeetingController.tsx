'use client';

import React, { useState } from 'react';
import {
  Video,
  Mic,
  MicOff,
  Camera,
  CameraOff,
  Compass,
  CheckCircle2,
  Clock,
  Sparkles,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';
import { api } from '../lib/api';
import { MeetJoinResult } from '../lib/types';
import { soundFX } from '../lib/sound';

interface MeetingControllerProps {
  initialUrl?: string;
}

export default function MeetingController({ initialUrl = '' }: MeetingControllerProps) {
  const [url, setUrl] = useState(initialUrl || 'https://meet.google.com/hsw-hmdc-gqc');
  const [displayName, setDisplayName] = useState('Meet Shah');
  const [muteMic, setMuteMic] = useState(true);
  const [disableCamera, setDisableCamera] = useState(false);
  const [autoJoin, setAutoJoin] = useState(true);
  const [browser, setBrowser] = useState('auto');
  const [isJoining, setIsJoining] = useState(false);
  const [joinResult, setJoinResult] = useState<MeetJoinResult | null>(null);

  const handleJoin = async () => {
    if (!url) return;
    setIsJoining(true);
    soundFX.playActionTone();

    try {
      const res = await api.joinMeeting({
        url,
        displayName,
        muteMic,
        disableCamera,
        autoJoin,
        browser,
      });
      setJoinResult(res);
      soundFX.playSuccessChime();
      api.speakText(`Successfully connected to meeting lobby. ${res.notes || ''}`);
    } catch (err: any) {
      soundFX.playActionTone();
      setJoinResult({
        status: 'FAILED',
        url,
        browser,
        lobby_handled: false,
        joined: false,
        in_call: false,
        notes: err?.message || 'Failed to connect to meeting agent.',
        duration_ms: 0,
      });
    } finally {
      setIsJoining(false);
    }
  };

  const sampleMeetings = [
    { name: 'Google Meet', url: 'https://meet.google.com/hsw-hmdc-gqc', type: 'Google Meet' },
    { name: 'Team Standup', url: 'https://meet.google.com/abc-defg-hij', type: 'Google Meet' },
    { name: 'Zoom Conference', url: 'https://zoom.us/j/9876543210', type: 'Zoom' },
    { name: 'Teams Room', url: 'https://teams.microsoft.com/l/meetup-join/19-sample', type: 'MS Teams' },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-3xl border border-cyan-500/20 relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 flex items-center justify-center text-cyan-400 border border-cyan-500/30">
              <Video className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Autonomous Meeting Agent
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  CDP High-Speed Connector
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Direct browser session attachment with automatic lobby permission handling and guest entry.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-900/60 px-3 py-1.5 rounded-xl border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Meeting Bridge Ready
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Main Configuration & Action Card */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel p-6 rounded-3xl space-y-5">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Compass className="w-4 h-4 text-cyan-400" />
              Target Session Configuration
            </h3>

            {/* URL Input */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Meeting Link (Google Meet / Zoom / Teams)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://meet.google.com/xxx-xxxx-xxx"
                  className="flex-1 glass-input px-4 py-3 rounded-2xl text-sm font-mono text-cyan-200"
                />
              </div>
            </div>

            {/* Display Name & Browser */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300">Guest Display Name</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Meet Shah"
                  className="w-full glass-input px-4 py-2.5 rounded-2xl text-sm"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300">Browser Engine</label>
                <select
                  value={browser}
                  onChange={(e) => setBrowser(e.target.value)}
                  className="w-full glass-input px-4 py-2.5 rounded-2xl text-sm bg-slate-900 text-slate-200"
                >
                  <option value="auto">Auto-Detect (Brave / Chrome / Edge)</option>
                  <option value="brave">Brave Browser (Preferred)</option>
                  <option value="chrome">Google Chrome</option>
                  <option value="edge">Microsoft Edge</option>
                </select>
              </div>
            </div>

            {/* Meeting Settings Toggles */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <button
                type="button"
                onClick={() => setMuteMic(!muteMic)}
                className={`p-3 rounded-2xl border flex items-center justify-between text-xs font-medium transition-all ${
                  muteMic
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                    : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                }`}
              >
                <span className="flex items-center gap-2">
                  {muteMic ? <MicOff className="w-4 h-4 text-rose-400" /> : <Mic className="w-4 h-4 text-emerald-400" />}
                  {muteMic ? 'Microphone Muted' : 'Microphone Live'}
                </span>
                <span className="text-[10px] uppercase font-mono">{muteMic ? 'ON' : 'OFF'}</span>
              </button>

              <button
                type="button"
                onClick={() => setDisableCamera(!disableCamera)}
                className={`p-3 rounded-2xl border flex items-center justify-between text-xs font-medium transition-all ${
                  disableCamera
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                    : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
                }`}
              >
                <span className="flex items-center gap-2">
                  {disableCamera ? <CameraOff className="w-4 h-4 text-rose-400" /> : <Camera className="w-4 h-4 text-cyan-400" />}
                  {disableCamera ? 'Camera Off' : 'Camera On'}
                </span>
                <span className="text-[10px] uppercase font-mono">{disableCamera ? 'OFF' : 'ON'}</span>
              </button>

              <button
                type="button"
                onClick={() => setAutoJoin(!autoJoin)}
                className={`p-3 rounded-2xl border flex items-center justify-between text-xs font-medium transition-all ${
                  autoJoin
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-slate-800/40 border-slate-700 text-slate-400'
                }`}
              >
                <span className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-emerald-400" />
                  Auto-Join Lobby
                </span>
                <span className="text-[10px] uppercase font-mono">{autoJoin ? 'ENABLED' : 'MANUAL'}</span>
              </button>
            </div>

            {/* Launch Button */}
            <button
              onClick={handleJoin}
              disabled={isJoining}
              className={`w-full py-3.5 rounded-2xl font-bold text-sm flex items-center justify-center gap-2.5 shadow-xl transition-all ${
                isJoining
                  ? 'bg-cyan-800 cursor-not-allowed text-cyan-200'
                  : 'bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-cyan-500/25 active:scale-[0.99]'
              }`}
            >
              {isJoining ? (
                <>
                  <Clock className="w-5 h-5 animate-spin" />
                  Autonomous Agent Entering Meeting...
                </>
              ) : (
                <>
                  <Video className="w-5 h-5" />
                  Auto-Join Meeting Now
                </>
              )}
            </button>
          </div>

          {/* Join Outcome Status Card */}
          {joinResult && (
            <div
              className={`glass-panel p-5 rounded-3xl border ${
                joinResult.joined
                  ? 'border-emerald-500/40 bg-emerald-950/20'
                  : 'border-rose-500/40 bg-rose-950/20'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  {joinResult.joined ? (
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  ) : (
                    <ShieldAlert className="w-6 h-6 text-rose-400" />
                  )}
                  <div>
                    <h4 className="font-bold text-white text-sm">
                      {joinResult.joined ? 'Active in Meeting Session' : 'Meeting Join Encountered Note'}
                    </h4>
                    <p className="text-xs text-slate-300 mt-0.5">{joinResult.notes}</p>
                  </div>
                </div>

                <div className="text-right text-xs font-mono text-slate-400">
                  <div>Status: <span className="text-emerald-400">{joinResult.status}</span></div>
                  <div>Latency: {joinResult.duration_ms} ms</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Col: Quick Sample Triggers & Capabilities */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-3xl space-y-4">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Quick Connect Presets
            </h3>
            <div className="space-y-2">
              {sampleMeetings.map((meet, idx) => (
                <div
                  key={idx}
                  onClick={() => setUrl(meet.url)}
                  className={`p-3 rounded-2xl border cursor-pointer transition-all ${
                    url === meet.url
                      ? 'bg-cyan-500/15 border-cyan-500/50 text-white'
                      : 'bg-slate-900/50 border-slate-800 text-slate-300 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold">{meet.name}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-cyan-300">
                      {meet.type}
                    </span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400 truncate mt-1 flex items-center gap-1">
                    <ExternalLink className="w-3 h-3" />
                    {meet.url}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-panel p-6 rounded-3xl space-y-3">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Autonomous Capabilities
            </h3>
            <ul className="text-xs text-slate-400 space-y-2 font-mono">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Auto-fills guest display name
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Mutes microphone before lobby entry
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Clicks "Ask to join" or "Join now"
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Bypasses Google Meet browser prompts
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
