export type VoiceState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING' | 'EXECUTING';

export interface VoiceCommandAction {
  id: string;
  command: string;
  recognizedText: string;
  actionTaken: string;
  status: 'SUCCESS' | 'EXECUTING' | 'FAILED';
  timestamp: string;
  details?: Record<string, unknown>;
}

export interface SubtaskItem {
  id: string;
  intent: string;
  phase: string;
  is_committed: boolean;
  tool?: string;
  output?: string;
}

export interface SwarmRunResult {
  session_id: string;
  phase: string;
  subtasks_total: number;
  evidence_passed: number;
  tokens_pruned: number;
  subtasks: SubtaskItem[];
}

export interface BlockItem {
  id: string;
  type: string;
  name: string;
  description: string;
  enabled: boolean;
  created_at?: string;
  execution_count?: number;
}

export interface DoctorCheck {
  name: string;
  status: 'PASS' | 'WARN' | 'FAIL';
  latency_ms: number;
  details: string;
}

export interface DoctorReport {
  overall_status: 'HEALTHY' | 'DEGRADED' | 'CRITICAL';
  checks: DoctorCheck[];
  timestamp: string;
  platform: string;
  summary: string;
}

export interface MCPToolItem {
  name: string;
  description: string;
  input_schema: {
    type: string;
    properties?: Record<string, { type: string; description?: string }>;
    required?: string[];
  };
}

export interface MeetJoinOptions {
  url: string;
  displayName?: string;
  muteMic?: boolean;
  disableCamera?: boolean;
  autoJoin?: boolean;
  browser?: string;
}

export interface MeetJoinResult {
  status: string;
  url: string;
  browser: string;
  lobby_handled: boolean;
  joined: boolean;
  in_call: boolean;
  notes: string;
  duration_ms: number;
}


export interface LiveKitConnectionInfo {
  url: string;
  room_name: string;
  identity: string;
  token: string;
  mode: string;
  server_active: boolean;
}
