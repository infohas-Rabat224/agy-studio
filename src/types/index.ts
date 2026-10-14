export type StudioMode = 'vibe_coding' | 'deep_thinking' | 'pedagogie' | 'creative' | 'tasks';

export type AgentType = 'antigravity' | 'hermes' | 'opencode' | 'claude' | 'codex' | 'qwen';

export interface AgentInfo {
  id: AgentType;
  name: string;
  status: 'Opérationnel' | 'Prêt' | 'Configuré' | 'En attente';
  color: string;
  description: string;
  defaultModel: string;
  capabilities: string[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent' | 'system';
  agentName?: string;
  text: string;
  timestamp: string;
  tokens?: number;
  latencyMs?: number;
  status?: 'success' | 'running' | 'error';
  diff?: {
    filePath: string;
    original: string;
    modified: string;
  };
  toolExecution?: {
    toolName: string;
    command?: string;
    output?: string;
    exitCode?: number;
  };
  attachments?: string[];
}

export interface WorkspaceFile {
  path: string;
  name: string;
  isDir: boolean;
  size?: number;
  language?: string;
  content?: string;
  children?: WorkspaceFile[];
}

export interface Session {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  pinned: boolean;
  favorite: boolean;
  status: 'active' | 'archived' | 'trash';
  messageCount: number;
  agent: AgentType;
  mode: StudioMode;
}

export interface GitCommit {
  hash: string;
  shortHash: string;
  message: string;
  author: string;
  date: string;
  branch: string;
}

export interface GitFileStatus {
  path: string;
  status: 'modified' | 'added' | 'deleted' | 'untracked';
  staged: boolean;
}

export interface AutonomyTask {
  id: string;
  title: string;
  priority: 'HIGH' | 'NORMAL' | 'LOW';
  status: 'ready' | 'in_progress' | 'blocked' | 'done';
  createdAt: string;
  assignedAgent?: AgentType;
  progressPercent?: number;
  logs?: string[];
}

export interface VaultSecret {
  id: string;
  key: string;
  value: string;
  provider: 'Gemini' | 'Anthropic' | 'OpenAI' | 'Cloudflare' | 'GitHub' | 'Custom';
  masked: boolean;
  updatedAt: string;
}

export interface MemoryItem {
  id: string;
  tier: 'episodic' | 'semantic' | 'procedural';
  title: string;
  content: string;
  tags: string[];
  accessCount: number;
  createdAt: string;
  confidence: number;
}

export interface ModelOption {
  id: string;
  name: string;
  provider: string;
  contextWindow: string;
  latency: string;
  description: string;
  badge: string;
  isDefault?: boolean;
}

export interface McpServer {
  id: string;
  name: string;
  category: 'wordpress' | 'vps' | 'github' | 'custom';
  status: 'connected' | 'idle' | 'error';
  endpoint: string;
  tools: string[];
}

export interface QuotaMetric {
  name: string;
  used: number;
  limit: number;
  unit: string;
  percent: number;
  resetIn: string;
}

export interface TimeMachineSnapshot {
  id: string;
  timestamp: string;
  prompt: string;
  agent: AgentType;
  filesChanged: string[];
  diffSummary: string;
}
