import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  StudioMode,
  AgentType,
  AgentInfo,
  Session,
  ChatMessage,
  WorkspaceFile,
  GitCommit,
  GitFileStatus,
  AutonomyTask,
  VaultSecret,
  MemoryItem,
  ModelOption,
  McpServer,
  QuotaMetric,
  TimeMachineSnapshot
} from '../types';
import {
  INITIAL_AGENTS,
  INITIAL_SESSIONS,
  INITIAL_FILES,
  INITIAL_MESSAGES,
  INITIAL_COMMITS,
  INITIAL_GIT_FILES,
  INITIAL_AUTONOMY_TASKS,
  INITIAL_VAULT_SECRETS,
  INITIAL_MEMORY_ITEMS,
  INITIAL_MODELS,
  INITIAL_MCP_SERVERS,
  INITIAL_QUOTAS,
  INITIAL_TIMEMACHINE_SNAPSHOTS
} from '../data/initialData';

export interface PreviewDoc {
  path: string;
  title: string;
  content: string;
  language: string;
  type: 'code' | 'doc' | 'pdf' | 'html';
  companionPdf?: boolean;
}

interface StudioContextType {
  // Modes & Agents
  currentMode: StudioMode;
  setCurrentMode: (mode: StudioMode) => void;
  currentAgent: AgentType;
  setCurrentAgent: (agent: AgentType) => void;
  agents: AgentInfo[];
  currentModel: string;
  setCurrentModel: (model: string) => void;
  models: ModelOption[];
  thinkingMode: 'turbo' | 'deep';
  setThinkingMode: (mode: 'turbo' | 'deep') => void;

  // Workspace & Sessions
  workspacePath: string;
  setWorkspacePath: (path: string) => void;
  sessions: Session[];
  activeSessionId: string;
  activeSession: Session;
  createSession: (title?: string) => void;
  switchSession: (id: string) => void;
  togglePinSession: (id: string) => void;
  toggleFavoriteSession: (id: string) => void;
  renameSession: (id: string, newTitle: string) => void;
  forkSession: (id: string) => void;
  deleteSession: (id: string) => void;

  // Messages
  messages: ChatMessage[];
  sendMessage: (text: string, attachments?: string[]) => void;
  isSending: boolean;
  clearMessages: () => void;

  // Files & Preview
  files: WorkspaceFile[];
  previewFile: PreviewDoc | null;
  setPreviewFile: (file: PreviewDoc | null) => void;
  openFileInPreview: (file: WorkspaceFile) => void;
  isPreviewOpen: boolean;
  setIsPreviewOpen: (open: boolean) => void;
  isPreviewAutofit: boolean;
  setIsPreviewAutofit: (autofit: boolean) => void;
  isSplitPreview: boolean;
  setIsSplitPreview: (split: boolean) => void;

  // Sidebar & Terminal Drawer
  isSidebarOpen: boolean;
  setIsSidebarOpen: (open: boolean) => void;
  isTerminalOpen: boolean;
  setIsTerminalOpen: (open: boolean) => void;
  terminalHistory: string[];
  executeTerminalCommand: (cmd: string) => void;
  clearTerminal: () => void;

  // Matrix Live Stream
  matrixLogs: string[];
  clearMatrixLogs: () => void;

  // Modals state
  activeModal: string | null;
  openModal: (modalName: string) => void;
  closeModal: () => void;

  // Git State
  gitCommits: GitCommit[];
  gitFiles: GitFileStatus[];
  gitBranch: string;
  gitCommitChanges: (message: string) => void;
  gitPush: () => void;
  gitPull: () => void;
  generateAiCommit: () => string;

  // Autonomy Tasks
  autonomyTasks: AutonomyTask[];
  addAutonomyTask: (title: string, priority: 'HIGH' | 'NORMAL' | 'LOW') => void;
  moveAutonomyTask: (id: string, newStatus: AutonomyTask['status']) => void;

  // Vault Secrets
  vaultSecrets: VaultSecret[];
  saveVaultSecret: (key: string, value: string, provider: VaultSecret['provider']) => void;
  deleteVaultSecret: (id: string) => void;
  toggleVaultSecretMask: (id: string) => void;

  // Memory
  memoryItems: MemoryItem[];
  addMemoryItem: (tier: MemoryItem['tier'], title: string, content: string, tags: string[]) => void;

  // MCP Servers
  mcpServers: McpServer[];
  addMcpServer: (name: string, category: McpServer['category'], endpoint: string) => void;

  // Quotas & Stats
  quotas: QuotaMetric[];
  timeMachineSnapshots: TimeMachineSnapshot[];
  rollbackSnapshot: (id: string) => void;

  // Language & UI
  language: 'fr' | 'en';
  setLanguage: (lang: 'fr' | 'en') => void;
  approvalBanner: { open: boolean; command: string } | null;
  setApprovalBanner: (banner: { open: boolean; command: string } | null) => void;
}

const StudioContext = createContext<StudioContextType | undefined>(undefined);

export const StudioProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentMode, setCurrentMode] = useState<StudioMode>('vibe_coding');
  const [currentAgent, setCurrentAgent] = useState<AgentType>('antigravity');
  const [agents] = useState<AgentInfo[]>(INITIAL_AGENTS);
  const [currentModel, setCurrentModel] = useState<string>('Gemini 3.8 Flash');
  const [models] = useState<ModelOption[]>(INITIAL_MODELS);
  const [thinkingMode, setThinkingMode] = useState<'turbo' | 'deep'>('turbo');
  const [language, setLanguage] = useState<'fr' | 'en'>('fr');

  const [workspacePath, setWorkspacePath] = useState<string>('C:\\Users\\Developer\\Documents\\gemini-projects');
  const [sessions, setSessions] = useState<Session[]>(INITIAL_SESSIONS);
  const [activeSessionId, setActiveSessionId] = useState<string>('sess-001');

  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [isSending, setIsSending] = useState<boolean>(false);

  const [files] = useState<WorkspaceFile[]>(INITIAL_FILES);
  const [previewFile, setPreviewFile] = useState<PreviewDoc | null>({
    path: 'cahier de text/ATAM_PROGRAMME_FORMATION_ET_HEURES.md',
    title: 'Programme Officiel ATAM (42 pages conformes)',
    content: `# Programme Officiel ATAM - Modules & Certifications\n- 7 Formateurs Référents\n- 42 pages de conformité réglementaire\n- Modules validés sans page blanche\n\n## Module 1 : Accueil et Intégration\nValidation des fiches techniques et progression pédagogique.\n\n## Module 2 : Développement Agentique & Vibecoding\nMaîtrise de l'environnement Agy Studio et déploiement continu.`,
    language: 'markdown',
    type: 'doc',
    companionPdf: true
  });
  const [isPreviewOpen, setIsPreviewOpen] = useState<boolean>(true);
  const [isPreviewAutofit, setIsPreviewAutofit] = useState<boolean>(false);
  const [isSplitPreview, setIsSplitPreview] = useState<boolean>(false);

  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [isTerminalOpen, setIsTerminalOpen] = useState<boolean>(false);
  const [terminalHistory, setTerminalHistory] = useState<string[]>([
    'Windows PowerShell v7.4.5',
    'Copyright (c) Microsoft Corporation. All rights reserved.',
    '',
    'Loading Agy Studio agentic environment...',
    '[OK] Native Win32 Folder Picker Bridge active on 127.0.0.1:8001',
    '[OK] Antigravity CLI connected (Gemini 3.8 Flash)',
    'PS C:\\Users\\Developer\\Documents\\gemini-projects> '
  ]);

  const [matrixLogs, setMatrixLogs] = useState<string[]>([
    '// Antigravity Kernel initialized. Live streaming ready.',
    '// Registered 130+ bundled agent skills from /skills',
    '// Bridge port 8001 listening for WinForms folder browser requests',
    '// Adaptive Intelligence: confidence engine calibrated to 96.4%'
  ]);

  const [activeModal, setActiveModal] = useState<string | null>(null);

  const [gitCommits, setGitCommits] = useState<GitCommit[]>(INITIAL_COMMITS);
  const [gitFiles, setGitFiles] = useState<GitFileStatus[]>(INITIAL_GIT_FILES);
  const [gitBranch] = useState<string>('main');

  const [autonomyTasks, setAutonomyTasks] = useState<AutonomyTask[]>(INITIAL_AUTONOMY_TASKS);
  const [vaultSecrets, setVaultSecrets] = useState<VaultSecret[]>(INITIAL_VAULT_SECRETS);
  const [memoryItems, setMemoryItems] = useState<MemoryItem[]>(INITIAL_MEMORY_ITEMS);
  const [mcpServers, setMcpServers] = useState<McpServer[]>(INITIAL_MCP_SERVERS);
  const [quotas] = useState<QuotaMetric[]>(INITIAL_QUOTAS);
  const [timeMachineSnapshots, setTimeMachineSnapshots] = useState<TimeMachineSnapshot[]>(INITIAL_TIMEMACHINE_SNAPSHOTS);
  const [approvalBanner, setApprovalBanner] = useState<{ open: boolean; command: string } | null>(null);

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];

  const openModal = (name: string) => setActiveModal(name);
  const closeModal = () => setActiveModal(null);

  const createSession = (customTitle?: string) => {
    const newId = `sess-${Date.now().toString().slice(-4)}`;
    const newSess: Session = {
      id: newId,
      title: customTitle || `Nouvelle Session #${sessions.length + 1}`,
      createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      updatedAt: 'À l\'instant',
      pinned: false,
      favorite: false,
      status: 'active',
      messageCount: 1,
      agent: currentAgent,
      mode: currentMode
    };
    setSessions([newSess, ...sessions]);
    setActiveSessionId(newId);
    setMessages([
      {
        id: `msg-${Date.now()}`,
        sender: 'agent',
        agentName: agents.find(a => a.id === currentAgent)?.name || 'Antigravity',
        text: `Session initialisée : **${newSess.title}**.\nMode actif : \`${currentMode}\` | Modèle : \`${currentModel}\`.\nQue pouvons-nous accomplir ensemble ?`,
        timestamp: new Date().toLocaleTimeString(),
        status: 'success'
      }
    ]);
  };

  const switchSession = (id: string) => {
    setActiveSessionId(id);
    const target = sessions.find(s => s.id === id);
    if (target) {
      setCurrentMode(target.mode);
      setCurrentAgent(target.agent);
    }
  };

  const togglePinSession = (id: string) => {
    setSessions(sessions.map(s => s.id === id ? { ...s, pinned: !s.pinned } : s));
  };

  const toggleFavoriteSession = (id: string) => {
    setSessions(sessions.map(s => s.id === id ? { ...s, favorite: !s.favorite } : s));
  };

  const renameSession = (id: string, newTitle: string) => {
    if (!newTitle.trim()) return;
    setSessions(sessions.map(s => s.id === id ? { ...s, title: newTitle.trim() } : s));
  };

  const forkSession = (id: string) => {
    const original = sessions.find(s => s.id === id);
    if (!original) return;
    const forkedId = `sess-fork-${Date.now().toString().slice(-4)}`;
    const forked: Session = {
      ...original,
      id: forkedId,
      title: `${original.title} (Fork)`,
      createdAt: 'À l\'instant',
      updatedAt: 'À l\'instant',
      pinned: false
    };
    setSessions([forked, ...sessions]);
    setActiveSessionId(forkedId);
  };

  const deleteSession = (id: string) => {
    if (sessions.length <= 1) return;
    const remaining = sessions.filter(s => s.id !== id);
    setSessions(remaining);
    if (activeSessionId === id) {
      setActiveSessionId(remaining[0].id);
    }
  };

  const openFileInPreview = (file: WorkspaceFile) => {
    setPreviewFile({
      path: file.path,
      title: file.name,
      content: file.content || `// Contenu du fichier ${file.path}`,
      language: file.language || 'text',
      type: file.name.endsWith('.md') ? 'doc' : 'code'
    });
    setIsPreviewOpen(true);
  };

  const sendMessage = (text: string, attachments?: string[]) => {
    if (!text.trim() && (!attachments || attachments.length === 0)) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString(),
      attachments
    };

    setMessages(prev => [...prev, userMsg]);
    setIsSending(true);

    // Add live stream log to matrix terminal
    setMatrixLogs(prev => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] DISPATCH -> Agent: ${currentAgent} (Model: ${currentModel})`,
      `[${new Date().toLocaleTimeString()}] Processing: "${text.slice(0, 40)}${text.length > 40 ? '...' : ''}"`
    ]);

    // Fast reactive agent response
    setTimeout(() => {
      const isQuotaQuery = text.includes('/quota');
      const isPlanQuery = text.includes('/plan');
      const isModelQuery = text.includes('/model');

      let replyText = `Action exécutée avec succès par **${agents.find(a => a.id === currentAgent)?.name}** !`;
      let toolExecution: ChatMessage['toolExecution'] = undefined;

      if (isQuotaQuery) {
        replyText = `### 📊 État des Quotas en Direct (Antigravity)\n- **RPM** : 18 / 300 (6% utilisé)\n- **TPM** : 48,500 / 1,000,000 (4.8%)\n- **RPD** : 1,240 / 10,000 (12.4%)\n\nLes limites sont optimales pour vos sessions de code.`;
      } else if (isPlanQuery) {
        replyText = `### 📋 Plan d'Exécution Structuré\n1. Analyser l'arborescence et valider l'intégrité du code.\n2. Exécuter les tests de non-régression.\n3. Vérifier la conformité des 42 pages de formation.\n4. Mettre à jour l'état Git et notifier via toast Windows 11.`;
      } else if (isModelQuery) {
        replyText = `Modèle actif : **${currentModel}**.\nPour changer, ouvrez la palette de modèles ou cliquez sur le sélecteur d'agent dans la barre supérieure.`;
      } else {
        replyText = `J'ai analysé votre demande : \n> "${text}"\n\nToutes les opérations ont été appliquées dans l'espace de travail local. Les fichiers et la mémoire adaptative ont été mis à jour sans régression.`;
        toolExecution = {
          toolName: 'antigravity_core_exec',
          command: `agy run --agent ${currentAgent} --workspace "${workspacePath}"`,
          output: `[SUCCESS] Output generated in 190ms\n[INTELLIGENCE] Pattern captured: +1 procedural memory item\n[GIT] Changes recorded on branch 'main'`,
          exitCode: 0
        };
      }

      const agentReply: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: 'agent',
        agentName: agents.find(a => a.id === currentAgent)?.name,
        text: replyText,
        timestamp: new Date().toLocaleTimeString(),
        tokens: Math.floor(Math.random() * 200) + 80,
        latencyMs: Math.floor(Math.random() * 250) + 120,
        status: 'success',
        toolExecution
      };

      setMessages(prev => [...prev, agentReply]);
      setIsSending(false);
      setMatrixLogs(prev => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] COMPLETED <- Agent returned status 200 (OK)`
      ]);
    }, 700);
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const executeTerminalCommand = (cmd: string) => {
    if (!cmd.trim()) return;
    setTerminalHistory(prev => [
      ...prev,
      `PS C:\\Users\\Developer\\Documents\\gemini-projects> ${cmd}`,
      `Executing command: ${cmd}...`,
      `[ExitCode: 0] Completed successfully.`
    ]);
  };

  const clearTerminal = () => {
    setTerminalHistory(['Terminal cleared.', 'PS C:\\Users\\Developer\\Documents\\gemini-projects> ']);
  };

  const clearMatrixLogs = () => {
    setMatrixLogs(['// Matrix stream cleared.']);
  };

  const gitCommitChanges = (message: string) => {
    if (!message.trim()) return;
    const newCommit: GitCommit = {
      hash: Math.random().toString(16).substring(2, 10),
      shortHash: Math.random().toString(16).substring(2, 9),
      message: message.trim(),
      author: agents.find(a => a.id === currentAgent)?.name || 'Antigravity Agent',
      date: 'À l\'instant',
      branch: gitBranch
    };
    setGitCommits([newCommit, ...gitCommits]);
    setGitFiles(gitFiles.map(f => ({ ...f, staged: false })));
  };

  const gitPush = () => {
    setMatrixLogs(prev => [...prev, `[GIT PUSH] Pushed commits to origin/${gitBranch} (Everything up-to-date)`]);
  };

  const gitPull = () => {
    setMatrixLogs(prev => [...prev, `[GIT PULL] Pulled changes from origin/${gitBranch}`]);
  };

  const generateAiCommit = () => {
    const prefixes = ['feat', 'fix', 'refactor', 'perf', 'docs'];
    const p = prefixes[Math.floor(Math.random() * prefixes.length)];
    return `${p}: update autonomous ide workspace components and adaptive intelligence state`;
  };

  const addAutonomyTask = (title: string, priority: 'HIGH' | 'NORMAL' | 'LOW') => {
    if (!title.trim()) return;
    const newTask: AutonomyTask = {
      id: `task-${Date.now().toString().slice(-4)}`,
      title: title.trim(),
      priority,
      status: 'ready',
      createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      assignedAgent: currentAgent,
      progressPercent: 0,
      logs: ['Tâche créée et ajoutée à la file d\'attente.']
    };
    setAutonomyTasks([newTask, ...autonomyTasks]);
  };

  const moveAutonomyTask = (id: string, newStatus: AutonomyTask['status']) => {
    setAutonomyTasks(autonomyTasks.map(t => {
      if (t.id === id) {
        return {
          ...t,
          status: newStatus,
          progressPercent: newStatus === 'done' ? 100 : newStatus === 'in_progress' ? 50 : t.progressPercent
        };
      }
      return t;
    }));
  };

  const saveVaultSecret = (key: string, value: string, provider: VaultSecret['provider']) => {
    const existing = vaultSecrets.find(s => s.key === key);
    if (existing) {
      setVaultSecrets(vaultSecrets.map(s => s.key === key ? { ...s, value, provider, updatedAt: 'À l\'instant' } : s));
    } else {
      const newSec: VaultSecret = {
        id: `sec-${Date.now().toString().slice(-4)}`,
        key,
        value,
        provider,
        masked: true,
        updatedAt: 'À l\'instant'
      };
      setVaultSecrets([...vaultSecrets, newSec]);
    }
  };

  const deleteVaultSecret = (id: string) => {
    setVaultSecrets(vaultSecrets.filter(s => s.id !== id));
  };

  const toggleVaultSecretMask = (id: string) => {
    setVaultSecrets(vaultSecrets.map(s => s.id === id ? { ...s, masked: !s.masked } : s));
  };

  const addMemoryItem = (tier: MemoryItem['tier'], title: string, content: string, tags: string[]) => {
    const newItem: MemoryItem = {
      id: `mem-${Date.now().toString().slice(-4)}`,
      tier,
      title,
      content,
      tags,
      accessCount: 1,
      createdAt: 'À l\'instant',
      confidence: 0.95
    };
    setMemoryItems([newItem, ...memoryItems]);
  };

  const addMcpServer = (name: string, category: McpServer['category'], endpoint: string) => {
    const newServer: McpServer = {
      id: `mcp-${Date.now().toString().slice(-4)}`,
      name,
      category,
      endpoint,
      status: 'connected',
      tools: ['execute_action', 'read_resource']
    };
    setMcpServers([...mcpServers, newServer]);
  };

  const rollbackSnapshot = (id: string) => {
    const snap = timeMachineSnapshots.find(s => s.id === id);
    if (!snap) return;
    setMatrixLogs(prev => [...prev, `[TIME-MACHINE] Rolled back to snapshot ${snap.id} (${snap.prompt})`]);
    closeModal();
  };

  return (
    <StudioContext.Provider
      value={{
        currentMode,
        setCurrentMode,
        currentAgent,
        setCurrentAgent,
        agents,
        currentModel,
        setCurrentModel,
        models,
        thinkingMode,
        setThinkingMode,
        workspacePath,
        setWorkspacePath,
        sessions,
        activeSessionId,
        activeSession,
        createSession,
        switchSession,
        togglePinSession,
        toggleFavoriteSession,
        renameSession,
        forkSession,
        deleteSession,
        messages,
        sendMessage,
        isSending,
        clearMessages,
        files,
        previewFile,
        setPreviewFile,
        openFileInPreview,
        isPreviewOpen,
        setIsPreviewOpen,
        isPreviewAutofit,
        setIsPreviewAutofit,
        isSplitPreview,
        setIsSplitPreview,
        isSidebarOpen,
        setIsSidebarOpen,
        isTerminalOpen,
        setIsTerminalOpen,
        terminalHistory,
        executeTerminalCommand,
        clearTerminal,
        matrixLogs,
        clearMatrixLogs,
        activeModal,
        openModal,
        closeModal,
        gitCommits,
        gitFiles,
        gitBranch,
        gitCommitChanges,
        gitPush,
        gitPull,
        generateAiCommit,
        autonomyTasks,
        addAutonomyTask,
        moveAutonomyTask,
        vaultSecrets,
        saveVaultSecret,
        deleteVaultSecret,
        toggleVaultSecretMask,
        memoryItems,
        addMemoryItem,
        mcpServers,
        addMcpServer,
        quotas,
        timeMachineSnapshots,
        rollbackSnapshot,
        language,
        setLanguage,
        approvalBanner,
        setApprovalBanner
      }}
    >
      {children}
    </StudioContext.Provider>
  );
};

export const useStudio = () => {
  const context = useContext(StudioContext);
  if (!context) {
    throw new Error('useStudio must be used within a StudioProvider');
  }
  return context;
};
