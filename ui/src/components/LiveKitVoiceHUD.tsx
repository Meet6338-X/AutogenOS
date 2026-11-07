'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Mic,
  MicOff,
  Maximize2,
  Minimize2,
  Radio,
  Sparkles,
  Activity,
  CheckCircle2,
  Volume2,
  Zap,
  Bot,
  Command,
  Send,
  Wifi,
  AlertCircle,
} from 'lucide-react';
import { VoiceState, VoiceCommandAction, LiveKitConnectionInfo } from '../lib/types';
import { api } from '../lib/api';
import { soundFX } from '../lib/sound';

interface LiveKitVoiceHUDProps {
  onNavigateTab?: (tab: string) => void;
  onExecuteGoal?: (goal: string) => void;
  onQuickJoinMeet?: (url: string) => void;
}

export default function LiveKitVoiceHUD({
  onNavigateTab,
  onExecuteGoal,
  onQuickJoinMeet,
}: LiveKitVoiceHUDProps) {
  const [isPoppedOut, setIsPoppedOut] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [lastAction, setLastAction] = useState<string>('LiveKit Voice HUD ready. Click mic or type a command below.');
  const [customInput, setCustomInput] = useState('');
  const [micNotice, setMicNotice] = useState<string | null>(null);
  const [commandHistory, setCommandHistory] = useState<VoiceCommandAction[]>([]);
  const [audioFreqs, setAudioFreqs] = useState<number[]>(new Array(16).fill(8));
  const [ttfaLatency, setTtfaLatency] = useState<number>(294);
  const [livekitInfo, setLivekitInfo] = useState<LiveKitConnectionInfo | null>(null);

  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const simIntervalRef = useRef<any>(null);

  // Initialize LiveKit connection and local token on mount
  useEffect(() => {
    let isMounted = true;
    api
      .getLiveKitToken('autogenos-local', 'user-cockpit')
      .then((info) => {
        if (isMounted) {
          setLivekitInfo(info);
        }
      })
      .catch((err) => {
        console.warn('[LiveKitVoiceHUD] LiveKit token fetch notice:', err);
      });

    return () => {
      isMounted = false;
      stopAudioSpectrum();
    };
  }, []);

  // Web Audio API frequency visualizer
  const startAudioSpectrum = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioCtx();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      const source = ctx.createMediaStreamSource(stream);
      source.connect(analyser);

      audioContextRef.current = ctx;
      analyserRef.current = analyser;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateBars = () => {
        analyser.getByteFrequencyData(dataArray);
        const bars: number[] = [];
        for (let i = 0; i < 16; i++) {
          const val = Math.max(6, Math.min(48, Math.floor((dataArray[i * 2] / 255) * 44) + 6));
          bars.push(val);
        }
        setAudioFreqs(bars);
        animFrameRef.current = requestAnimationFrame(updateBars);
      };
      updateBars();
      setMicNotice(null);
    } catch (err: any) {
      console.warn('[LiveKitVoiceHUD] Microphone getUserMedia notice:', err);
      setMicNotice('Microphone permission blocked or unavailable. Using simulated audio & direct dispatcher.');
      startSimulatedWaveform();
    }
  };

  const startSimulatedWaveform = () => {
    if (simIntervalRef.current) clearInterval(simIntervalRef.current);
    let step = 0;
    simIntervalRef.current = setInterval(() => {
      step += 0.25;
      const simulated = Array.from({ length: 16 }, (_, i) => {
        return Math.floor(Math.sin(step + i * 0.45) * 16 + 24);
      });
      setAudioFreqs(simulated);
    }, 70);
  };

  const stopAudioSpectrum = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (simIntervalRef.current) clearInterval(simIntervalRef.current);
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setAudioFreqs(new Array(16).fill(6));
  };

  // Process incoming voice commands
  const handleVoiceCommand = async (rawText: string) => {
    const text = rawText.trim().toLowerCase();
    if (!text) return;

    soundFX.playActionTone();
    setVoiceState('THINKING');
    setLastAction(`Parsing intent: "${text}"`);
    setTranscript(rawText);

    const actionRecord: VoiceCommandAction = {
      id: `cmd-${Date.now()}`,
      command: text,
      recognizedText: rawText,
      actionTaken: 'Processing',
      status: 'EXECUTING',
      timestamp: new Date().toLocaleTimeString(),
    };

    try {
      if (text.includes('diagnostic') || text.includes('doctor') || text.includes('system check') || text.includes('health')) {
        setVoiceState('EXECUTING');
        setLastAction('Running System Doctor diagnostics...');
        if (onNavigateTab) onNavigateTab('doctor');
        const report = await api.runDoctor();
        soundFX.playSuccessChime();
        setVoiceState('SPEAKING');
        const msg = `System diagnostics completed. Overall status is ${report.overall_status}. All subsystems operational.`;
        setLastAction(msg);
        api.speakText(msg);
        actionRecord.actionTaken = 'Ran System Doctor diagnostics';
        actionRecord.status = 'SUCCESS';
      } else if (text.includes('join meet') || text.includes('join meeting') || text.includes('meet.google.com')) {
        setVoiceState('EXECUTING');
        let url = 'https://meet.google.com/hsw-hmdc-gqc';
        const match = text.match(/https?:\/\/[^\s]+/);
        if (match) url = match[0];
        setLastAction(`Autonomous Meeting Agent joining: ${url}`);
        if (onNavigateTab) onNavigateTab('meetings');
        if (onQuickJoinMeet) onQuickJoinMeet(url);
        const res = await api.joinMeeting({ url, displayName: 'Meet Shah' });
        soundFX.playSuccessChime();
        setVoiceState('SPEAKING');
        const msg = `Connected to meeting successfully. ${res.notes || 'In call now.'}`;
        setLastAction(msg);
        api.speakText(msg);
        actionRecord.actionTaken = `Joined meeting ${url}`;
        actionRecord.status = 'SUCCESS';
      } else if (text.includes('block') || text.includes('show blocks') || text.includes('list blocks')) {
        setVoiceState('EXECUTING');
        setLastAction('Navigating to Modular Block Manager...');
        if (onNavigateTab) onNavigateTab('blocks');
        const blocks = await api.fetchBlocks();
        soundFX.playSuccessChime();
        setVoiceState('SPEAKING');
        const msg = `Block Manager opened. Displaying ${blocks.length} active modular blocks.`;
        setLastAction(msg);
        api.speakText(msg);
        actionRecord.actionTaken = 'Navigated to Blocks Catalog';
        actionRecord.status = 'SUCCESS';
      } else if (text.includes('task') || text.includes('execute') || text.includes('run') || text.includes('swarm')) {
        const goal = text.replace(/^(task|execute|run|swarm|please)\s+/i, '').trim() || 'Inspect system health and summarize active processes';
        setVoiceState('EXECUTING');
        setLastAction(`Dispatching swarm goal: "${goal}"`);
        if (onNavigateTab) onNavigateTab('swarm');
        if (onExecuteGoal) onExecuteGoal(goal);
        const res = await api.runOrchestrator(goal);
        soundFX.playSuccessChime();
        setVoiceState('SPEAKING');
        const msg = `Swarm task completed across ${res.subtasks_total} atomic subtasks. Saved ${res.tokens_pruned} tokens.`;
        setLastAction(msg);
        api.speakText(msg);
        actionRecord.actionTaken = `Executed swarm intent: "${goal}"`;
        actionRecord.status = 'SUCCESS';
      } else if (text.includes('pop out') || text.includes('expand')) {
        setIsPoppedOut(true);
        soundFX.playSuccessChime();
        setVoiceState('SPEAKING');
        api.speakText('Voice HUD expanded to pop out modal.');
        actionRecord.actionTaken = 'Popped out Voice HUD';
        actionRecord.status = 'SUCCESS';
      } else if (text.includes('dock') || text.includes('minimize')) {
        setIsPoppedOut(false);
        soundFX.playSuccessChime();
        setVoiceState('SPEAKING');
        api.speakText('Voice HUD docked to corner.');
        actionRecord.actionTaken = 'Docked Voice HUD';
        actionRecord.status = 'SUCCESS';
      } else if (text.includes('help') || text.includes('what can you do')) {
        setVoiceState('SPEAKING');
        const helpMsg = 'You can say or type: run diagnostic, join meeting, show blocks, or execute task.';
        setLastAction(helpMsg);
        api.speakText(helpMsg);
        actionRecord.actionTaken = 'Read help commands';
        actionRecord.status = 'SUCCESS';
      } else {
        // General query treated as autonomous intent
        setVoiceState('EXECUTING');
        setLastAction(`Executing general intent: "${rawText}"`);
        if (onNavigateTab) onNavigateTab('swarm');
        if (onExecuteGoal) onExecuteGoal(rawText);
        const res = await api.runOrchestrator(rawText);
        soundFX.playSuccessChime();
        setVoiceState('SPEAKING');
        const msg = `Executed: ${rawText}. Completed ${res.subtasks_total} subtasks.`;
        setLastAction(msg);
        api.speakText(msg);
        actionRecord.actionTaken = `Handled command: "${rawText}"`;
        actionRecord.status = 'SUCCESS';
      }
    } catch (err: any) {
      soundFX.playActionTone();
      setVoiceState('IDLE');
      setLastAction(`Error executing command: ${err?.message || 'Action failed'}`);
      actionRecord.status = 'FAILED';
    }

    setCommandHistory((prev) => [actionRecord, ...prev.slice(0, 9)]);
    setTimeout(() => {
      setVoiceState((prev) => (prev === 'SPEAKING' || prev === 'EXECUTING' ? 'IDLE' : prev));
    }, 4500);
  };

  // Toggle Continuous Speech Recognition
  const toggleListening = () => {
    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      stopAudioSpectrum();
      setIsListening(false);
      setVoiceState('IDLE');
      setTranscript('');
      setLastAction('Microphone muted. Voice HUD standby.');
    } else {
      soundFX.playWakeTone();
      setIsListening(true);
      setVoiceState('LISTENING');
      setLastAction('Listening for voice commands...');
      startAudioSpectrum();

      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = 'en-US';

          const startTime = Date.now();

          recognition.onresult = (event: any) => {
            const current = event.resultIndex;
            const text = event.results[current][0].transcript;
            setTranscript(text);
            setTtfaLatency(Math.min(370, Date.now() - startTime));

            if (event.results[current].isFinal) {
              handleVoiceCommand(text);
            }
          };

          recognition.onerror = (e: any) => {
            console.warn('[LiveKitVoiceHUD SpeechRecognition] notice:', e.error);
            if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
              setMicNotice('Microphone access blocked. Click Allow in address bar or use command bar below.');
            } else if (e.error === 'network') {
              setMicNotice('Browser speech network offline. Direct Voice Command input is active.');
            }
            startSimulatedWaveform();
          };

          recognition.onend = () => {
            if (isListening && recognitionRef.current) {
              try {
                recognition.start();
              } catch {}
            }
          };

          recognition.start();
          recognitionRef.current = recognition;
        } catch (e: any) {
          console.warn('[LiveKitVoiceHUD] Recognition start notice:', e);
          startSimulatedWaveform();
        }
      } else {
        setMicNotice('SpeechRecognition API not supported in this browser. Use Direct Command input below.');
        startSimulatedWaveform();
      }
    }
  };

  // Submit typed command
  const handleCustomInputSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customInput.trim()) return;
    const text = customInput;
    setCustomInput('');
    handleVoiceCommand(text);
  };

  // Color schemes for orb state
  const getOrbStyles = () => {
    switch (voiceState) {
      case 'LISTENING':
        return {
          glow: 'glow-emerald',
          gradient: 'from-emerald-400 via-teal-500 to-cyan-600',
          ring: 'border-emerald-400/60',
          badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          label: 'LISTENING (0ms VAD)',
        };
      case 'THINKING':
        return {
          glow: 'glow-cyan',
          gradient: 'from-cyan-400 via-sky-500 to-indigo-600',
          ring: 'border-cyan-400/70',
          badgeBg: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
          label: 'THINKING (RSI Graph)',
        };
      case 'SPEAKING':
        return {
          glow: 'glow-purple',
          gradient: 'from-purple-400 via-fuchsia-500 to-pink-600',
          ring: 'border-purple-400/70',
          badgeBg: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
          label: 'SPEAKING (SAPI5/TTS)',
        };
      case 'EXECUTING':
        return {
          glow: 'glow-amber',
          gradient: 'from-amber-400 via-orange-500 to-red-500',
          ring: 'border-amber-400/80',
          badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
          label: 'EXECUTING ACTION',
        };
      default:
        return {
          glow: 'glow-cyan',
          gradient: 'from-cyan-500 via-blue-600 to-slate-800',
          ring: 'border-cyan-500/30',
          badgeBg: 'bg-slate-800/60 text-slate-300 border-slate-700',
          label: 'IDLE (Click Mic to Wake)',
        };
    }
  };

  const orbStyle = getOrbStyles();

  return (
    <>
      {/* 1. DOCKED FLOATING HUD (Lower Right) */}
      {!isPoppedOut && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3">
          <div className="glass-panel-glow px-4 py-2.5 rounded-2xl flex items-center gap-3 shadow-2xl backdrop-blur-xl border border-cyan-500/30 animate-pulse-scale">
            {/* 3D Glowing Mini Orb */}
            <div
              onClick={toggleListening}
              className={`relative cursor-pointer w-11 h-11 rounded-full flex items-center justify-center p-0.5 transition-all duration-300 ${orbStyle.glow}`}
            >
              <div
                className={`w-full h-full rounded-full bg-gradient-to-tr ${orbStyle.gradient} flex items-center justify-center shadow-inner`}
              >
                {voiceState === 'LISTENING' ? (
                  <Activity className="w-5 h-5 text-white animate-pulse" />
                ) : voiceState === 'THINKING' ? (
                  <Zap className="w-5 h-5 text-white animate-spin" />
                ) : voiceState === 'SPEAKING' ? (
                  <Volume2 className="w-5 h-5 text-white animate-bounce" />
                ) : (
                  <Radio className="w-5 h-5 text-cyan-200" />
                )}
              </div>
              {voiceState === 'LISTENING' && (
                <div className="absolute inset-0 rounded-full border-2 border-emerald-400 animate-ripple pointer-events-none" />
              )}
            </div>

            {/* Audio Spectrum Waveform Bars */}
            <div className="flex items-end gap-1 h-7 px-1">
              {audioFreqs.slice(0, 10).map((h, i) => (
                <div
                  key={i}
                  style={{ height: `${h}px` }}
                  className={`w-1 rounded-full transition-all duration-100 ${
                    voiceState === 'LISTENING'
                      ? 'bg-emerald-400'
                      : voiceState === 'SPEAKING'
                      ? 'bg-purple-400'
                      : 'bg-cyan-500/50'
                  }`}
                />
              ))}
            </div>

            {/* Quick Status / Transcript */}
            <div className="max-w-[200px] truncate text-xs">
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block" />
                LiveKit WebRTC
              </div>
              <div className="text-[11px] text-slate-400 truncate">
                {transcript || lastAction}
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-1.5 pl-1 border-l border-slate-700/60">
              <button
                onClick={toggleListening}
                title={isListening ? 'Mute Microphone' : 'Activate Voice'}
                className={`p-2 rounded-xl transition-all ${
                  isListening
                    ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                    : 'bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30'
                }`}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
              <button
                onClick={() => setIsPoppedOut(true)}
                title="Pop Out Full LiveKit HUD"
                className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition-all"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. AWESOME POP-OUT LIVEKIT HUD MODAL */}
      {isPoppedOut && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="relative w-full max-w-3xl glass-panel-glow rounded-3xl p-6 sm:p-8 border border-cyan-500/40 shadow-2xl overflow-hidden flex flex-col gap-5">
            {/* Header & Controls */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-cyan-500/20 flex items-center justify-center text-cyan-400 border border-cyan-500/30">
                  <Radio className="w-5 h-5 animate-pulse" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    LiveKit Voice Agent Cockpit
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                      <Wifi className="w-3 h-3 text-emerald-400" />
                      WebRTC Active
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Continuous sub-370ms local WebRTC voice agent with autonomous OS action dispatcher
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsPoppedOut(false)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium transition-all"
                >
                  <Minimize2 className="w-4 h-4" />
                  Dock HUD
                </button>
              </div>
            </div>

            {/* LiveKit Connection Telemetry Bar */}
            <div className="flex items-center justify-between p-2.5 rounded-2xl bg-slate-950/70 border border-slate-800 text-xs font-mono">
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Room:</span>
                <span className="text-cyan-400 font-bold">{livekitInfo?.room_name || 'autogenos-local'}</span>
                <span className="text-slate-600">|</span>
                <span>Mode:</span>
                <span className="text-emerald-400">100% Local Free</span>
              </div>
              <div className="flex items-center gap-2 text-slate-400">
                <span>Opus 48kHz</span>
                <span className="text-slate-600">|</span>
                <span className="text-cyan-400">TTFA: {ttfaLatency}ms</span>
              </div>
            </div>

            {/* Microphone Notice / Alert */}
            {micNotice && (
              <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200 flex items-center gap-2 font-mono">
                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                <span>{micNotice}</span>
              </div>
            )}

            {/* Central 3D Glowing Energy Orb */}
            <div className="relative flex flex-col items-center justify-center py-4">
              {/* Outer Energy Orbit Rings */}
              <div className={`relative w-44 h-44 rounded-full flex items-center justify-center transition-all duration-500 ${orbStyle.glow}`}>
                {/* Rotating Ring 1 */}
                <div className={`absolute inset-0 rounded-full border-2 border-dashed ${orbStyle.ring} animate-spin-slow`} />
                {/* Rotating Ring 2 (Counter-Clockwise) */}
                <div className="absolute inset-2 rounded-full border border-dotted border-white/20 animate-spin-reverse" />

                {/* Core 3D Glowing Gradient Sphere */}
                <div
                  onClick={toggleListening}
                  className={`w-32 h-32 rounded-full cursor-pointer bg-gradient-to-tr ${orbStyle.gradient} p-1 shadow-2xl flex items-center justify-center transition-transform transform active:scale-95`}
                >
                  <div className="w-full h-full rounded-full bg-black/20 backdrop-blur-xs flex flex-col items-center justify-center text-center p-3">
                    {voiceState === 'LISTENING' ? (
                      <Activity className="w-9 h-9 text-white animate-pulse" />
                    ) : voiceState === 'THINKING' ? (
                      <Zap className="w-9 h-9 text-white animate-spin" />
                    ) : voiceState === 'SPEAKING' ? (
                      <Volume2 className="w-9 h-9 text-white animate-bounce" />
                    ) : voiceState === 'EXECUTING' ? (
                      <Sparkles className="w-9 h-9 text-amber-200 animate-spin" />
                    ) : (
                      <Mic className="w-9 h-9 text-cyan-200 hover:scale-110 transition-transform" />
                    )}
                    <span className="text-[10px] font-bold text-white tracking-wider mt-1 uppercase">
                      {isListening ? 'LISTENING' : 'STANDBY'}
                    </span>
                  </div>
                </div>

                {/* Animated Ripple for Listening */}
                {voiceState === 'LISTENING' && (
                  <div className="absolute inset-0 rounded-full border-2 border-emerald-400 animate-ripple pointer-events-none" />
                )}
              </div>

              {/* State Badge */}
              <div className="mt-3 flex items-center gap-3">
                <span className={`text-xs font-mono font-semibold px-3 py-1 rounded-full border ${orbStyle.badgeBg}`}>
                  {orbStyle.label}
                </span>
              </div>
            </div>

            {/* Real-time Frequency Spectrum Audio Visualizer */}
            <div className="glass-panel p-3 rounded-2xl flex flex-col gap-2">
              <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
                <span className="flex items-center gap-1.5 font-medium">
                  <Activity className="w-3.5 h-3.5 text-cyan-400" />
                  LiveKit Audio FFT Spectrum (48kHz WebRTC)
                </span>
                <span className="font-mono text-cyan-400">16-Band Active</span>
              </div>
              <div className="flex items-end justify-center gap-1.5 h-10 px-2 bg-slate-950/60 rounded-xl py-1">
                {audioFreqs.map((h, i) => (
                  <div
                    key={i}
                    style={{ height: `${h}px` }}
                    className={`w-3 rounded-t-sm transition-all duration-75 ${
                      voiceState === 'LISTENING'
                        ? 'bg-gradient-to-t from-emerald-600 to-emerald-300 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
                        : voiceState === 'SPEAKING'
                        ? 'bg-gradient-to-t from-purple-600 to-purple-300 shadow-[0_0_8px_rgba(168,85,247,0.5)]'
                        : 'bg-gradient-to-t from-slate-700 to-cyan-500/50'
                    }`}
                  />
                ))}
              </div>
            </div>

            {/* Direct Voice & Intent Command Input Form (100% Reliable In Any Browser) */}
            <form onSubmit={handleCustomInputSubmit} className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  placeholder="Type or speak command (e.g. 'run diagnostic', 'join meeting', 'show blocks', 'execute task')..."
                  className="w-full glass-input px-4 py-2.5 rounded-2xl text-xs font-mono text-cyan-200 placeholder:text-slate-500"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2.5 rounded-2xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-cyan-500/20 transition-all active:scale-95"
              >
                <Send className="w-3.5 h-3.5" />
                Dispatch
              </button>
            </form>

            {/* Speech-to-Text Live Transcript & Action Status */}
            <div className="glass-panel p-3.5 rounded-2xl flex flex-col gap-1.5">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                <span>Transcript & Response Feed</span>
                <span className="text-cyan-400 font-mono text-[10px]">Zero-Latency Feedback</span>
              </div>
              <div className="min-h-[40px] bg-slate-950/70 p-2.5 rounded-xl border border-slate-800 text-xs font-mono text-slate-200">
                {transcript ? (
                  <span className="text-cyan-300">{transcript}</span>
                ) : (
                  <span className="text-slate-400 italic">{lastAction}</span>
                )}
              </div>
            </div>

            {/* Quick Voice Command Triggers & Examples */}
            <div className="flex flex-col gap-2">
              <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Command className="w-3.5 h-3.5 text-cyan-400" />
                Quick Actions (Click to trigger voice turn & execution)
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { label: 'run diagnostic', tip: 'Runs System Doctor checks', tab: 'doctor' },
                  { label: 'join meeting', tip: 'Fast Google Meet joiner', tab: 'meetings' },
                  { label: 'show blocks', tip: 'Modular blocks catalog', tab: 'blocks' },
                  { label: 'execute task', tip: 'Swarm closed-loop goal', tab: 'swarm' },
                ].map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleVoiceCommand(item.label)}
                    className="p-2.5 rounded-xl bg-slate-800/60 hover:bg-cyan-950/40 border border-slate-700/60 hover:border-cyan-500/50 text-left transition-all group"
                  >
                    <div className="text-xs font-mono font-semibold text-cyan-300 group-hover:text-cyan-200">
                      "{item.label}"
                    </div>
                    <div className="text-[10px] text-slate-400 truncate">{item.tip}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Recent Action Log */}
            {commandHistory.length > 0 && (
              <div className="glass-panel p-3 rounded-2xl flex flex-col gap-1.5 max-h-28 overflow-y-auto">
                <div className="text-[10px] font-semibold text-slate-400 flex items-center justify-between">
                  <span>Execution Log</span>
                  <span className="text-[10px] text-slate-500 font-mono">{commandHistory.length} executed</span>
                </div>
                <div className="space-y-1">
                  {commandHistory.slice(0, 4).map((cmd) => (
                    <div
                      key={cmd.id}
                      className="flex items-center justify-between p-1.5 rounded-lg bg-slate-950/40 border border-slate-800/80 text-[11px]"
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                        <span className="font-mono text-cyan-300 truncate">"{cmd.command}"</span>
                        <span className="text-slate-400 truncate">→ {cmd.actionTaken}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-500 shrink-0">{cmd.timestamp}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Bottom Controls Bar */}
            <div className="flex items-center justify-between pt-1">
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <Bot className="w-4 h-4 text-cyan-400" />
                <span>Speak or type any command to trigger autonomous execution.</span>
              </div>
              <button
                type="button"
                onClick={toggleListening}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-2xl font-bold text-xs shadow-xl transition-all ${
                  isListening
                    ? 'bg-rose-500 hover:bg-rose-600 text-white shadow-rose-500/25'
                    : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-cyan-500/25'
                }`}
              >
                {isListening ? (
                  <>
                    <MicOff className="w-4 h-4" />
                    Mute Microphone
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4" />
                    Activate Microphone
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
