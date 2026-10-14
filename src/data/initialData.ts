import {
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

export const INITIAL_AGENTS: AgentInfo[] = [
  {
    id: 'antigravity',
    name: 'Antigravity (Local)',
    status: 'Opérationnel',
    color: 'emerald',
    description: 'Moteur central Google Antigravity connecté au CLI local agy.exe.',
    defaultModel: 'Gemini 3.8 Flash',
    capabilities: ['Autonomous Coding', 'Bash/PowerShell PTY', 'AST Graph', 'Diff Apply']
  },
  {
    id: 'hermes',
    name: 'Hermes Agent',
    status: 'Prêt',
    color: 'sky',
    description: 'Agent d\'orchestration rapide et de délégation de sous-tâches.',
    defaultModel: 'Gemini 3.8 Flash',
    capabilities: ['Subagent Spawning', 'Session Lineage', 'Multi-file Read']
  },
  {
    id: 'opencode',
    name: 'OpenCode',
    status: 'Prêt',
    color: 'indigo',
    description: 'Spécialiste de la génération de code robuste et de l\'analyse statique.',
    defaultModel: 'Gemini 3.1 Pro',
    capabilities: ['Type Checking', 'Refactoring', 'Unit Tests']
  },
  {
    id: 'claude',
    name: 'Claude Code CLI',
    status: 'Configuré',
    color: 'amber',
    description: 'Moteur Anthropic Claude pour le raisonnement architectural profond.',
    defaultModel: 'Claude 3.7 Sonnet',
    capabilities: ['Deep Architecture', 'Complex Refactor', 'System Audits']
  },
  {
    id: 'codex',
    name: 'Codex Engine',
    status: 'Prêt',
    color: 'purple',
    description: 'Optimisation algorithmique et conversion multi-langages.',
    defaultModel: 'Codex Alpha',
    capabilities: ['Polyglot Translation', 'Performance Benchmarks']
  },
  {
    id: 'qwen',
    name: 'Qwen Coder',
    status: 'En attente',
    color: 'teal',
    description: 'Grand modèle open-weights spécialisé dans l\'autonomie de code.',
    defaultModel: 'Qwen 2.5 Coder 32B',
    capabilities: ['Offline Inference', 'Code Synthesis']
  }
];

export const INITIAL_SESSIONS: Session[] = [
  {
    id: 'sess-001',
    title: 'Agy Studio v2.6 — Migration & Command Center',
    createdAt: '2026-10-14 09:30',
    updatedAt: '2026-10-14 10:15',
    pinned: true,
    favorite: true,
    status: 'active',
    messageCount: 8,
    agent: 'antigravity',
    mode: 'vibe_coding'
  },
  {
    id: 'sess-002',
    title: 'Pédagogie ATAM — Dossiers Formateurs & 42 Pages',
    createdAt: '2026-10-13 16:45',
    updatedAt: '2026-10-13 18:20',
    pinned: true,
    favorite: false,
    status: 'active',
    messageCount: 14,
    agent: 'antigravity',
    mode: 'pedagogie'
  },
  {
    id: 'sess-003',
    title: 'Ghost Mode & Background Tasks Daemon',
    createdAt: '2026-10-12 11:10',
    updatedAt: '2026-10-12 12:05',
    pinned: false,
    favorite: true,
    status: 'active',
    messageCount: 6,
    agent: 'hermes',
    mode: 'tasks'
  },
  {
    id: 'sess-004',
    title: 'Audit Sécurité .env Vault & Masquage Clés',
    createdAt: '2026-10-10 14:00',
    updatedAt: '2026-10-10 14:35',
    pinned: false,
    favorite: false,
    status: 'archived',
    messageCount: 5,
    agent: 'claude',
    mode: 'deep_thinking'
  }
];

export const INITIAL_FILES: WorkspaceFile[] = [
  {
    path: 'backend/server.py',
    name: 'server.py',
    isDir: false,
    size: 131397,
    language: 'python',
    content: `# Agy Studio Core Server (FastAPI + PTY + Adaptive Intelligence)
import os, sys
from fastapi import FastAPI
app = FastAPI(title="Agy Studio Agentic API", version="2.6.0")
`
  },
  {
    path: 'backend/advanced_features.py',
    name: 'advanced_features.py',
    isDir: false,
    size: 24500,
    language: 'python',
    content: `# Advanced Features Router: Monaco diffs, visual git, and Win11 toasts`
  },
  {
    path: 'backend/intelligence/learning_engine.py',
    name: 'learning_engine.py',
    isDir: false,
    size: 18200,
    language: 'python',
    content: `# Adaptive Intelligence Engine: Real-time pattern distillation and strategy extraction`
  },
  {
    path: 'cahier de text/ATAM_PROGRAMME_FORMATION_ET_HEURES.md',
    name: 'ATAM_PROGRAMME_FORMATION_ET_HEURES.md',
    isDir: false,
    size: 54000,
    language: 'markdown',
    content: `# Programme Officiel ATAM - Modules & Certifications
- 7 Formateurs Référents
- 42 pages de conformité réglementaire
- Modules validés sans page blanche`
  },
  {
    path: 'README.md',
    name: 'README.md',
    isDir: false,
    size: 8545,
    language: 'markdown',
    content: `# ⚡ Agy Studio
The Ultimate Native Autonomous IDE, Workspace Control Plane & UI for Google Antigravity.`
  },
  {
    path: 'tasks/QUEUE.md',
    name: 'QUEUE.md',
    isDir: false,
    size: 3200,
    language: 'markdown',
    content: `# Ghost Mode Autonomous Queue
- [x] Initialiser le pont WinForms sur le port 8001
- [ ] Optimiser la vectorisation de la mémoire procédurale
- [ ] Générer le rapport consolidé de session`
  }
];

export const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-1',
    sender: 'agent',
    agentName: 'Antigravity (Local)',
    text: `Bienvenue dans **Agy Studio v2.6** — Votre Command Center Agentique & Intelligence Adaptative !

Tous les moteurs locaux (CLI Antigravity \`agy\`, Pont natif Win32 port 8001, Monaco Editor, PTY PowerShell et 130+ compétences) sont opérationnels.

Quel projet souhaitez-vous inspecter ou développer aujourd'hui ?`,
    timestamp: '10:00:15',
    tokens: 142,
    latencyMs: 180,
    status: 'success'
  },
  {
    id: 'msg-2',
    sender: 'user',
    text: `Vérifie la santé des agents, l'état du pont port 8001 et le catalogue de mémoire adaptative.`,
    timestamp: '10:01:02'
  },
  {
    id: 'msg-3',
    sender: 'agent',
    agentName: 'Antigravity (Local)',
    text: `### 🔍 Diagnostic d'Intégrité Système — Agy Studio v2.6

1. **Pont Natif WinForms (Port 8001)** : Actif et en écoute (Ping: 4ms). Sélecteur de dossiers Windows prêt.
2. **Orchestrateur & Agents** :
   - \`Antigravity\` : Opérationnel (Gemini 3.8 Flash, quota 94.2% disponible).
   - \`Hermes\` : Prêt pour délégation de sous-agents.
   - \`Claude Code\` : Configuré pour le raisonnement architectural.
3. **Moteur d'Apprentissage Actif** : Score de confiance global à **96.4%** sur 42 stratégies validées.
4. **Catalogue Mémoire 3-Tier** :
   - Épisodique : 128 sessions indexées.
   - Sémantique : 450 concepts techniques.
   - Procédurale : 34 workflows auto-générés sans régression.`,
    timestamp: '10:01:14',
    tokens: 384,
    latencyMs: 240,
    status: 'success',
    toolExecution: {
      toolName: 'diagnostic_suite',
      command: 'agy diagnostic --all-agents --check-bridge',
      output: '[OK] Bridge: 127.0.0.1:8001 listening\n[OK] Antigravity CLI v2.6 initialized\n[OK] Memory guard passed (0 corruption detected)',
      exitCode: 0
    }
  }
];

export const INITIAL_COMMITS: GitCommit[] = [
  {
    hash: '7f91a2bc',
    shortHash: '7f91a2b',
    message: 'feat: add reactive command center header with 5 compact selectors',
    author: 'Antigravity Agent',
    date: '2026-10-14 09:45',
    branch: 'main'
  },
  {
    hash: 'a3d8194e',
    shortHash: 'a3d8194',
    message: 'refactor: integrate Monaco editor and split-diff preview pane',
    author: 'Claude Code',
    date: '2026-10-13 17:20',
    branch: 'main'
  },
  {
    hash: 'e50c418f',
    shortHash: 'e50c418',
    message: 'fix: ensure native folder picker bridge fallback for remote environments',
    author: 'Hermes Agent',
    date: '2026-10-12 14:10',
    branch: 'main'
  }
];

export const INITIAL_GIT_FILES: GitFileStatus[] = [
  { path: 'backend/server.py', status: 'modified', staged: true },
  { path: 'src/App.tsx', status: 'modified', staged: true },
  { path: 'tasks/QUEUE.md', status: 'modified', staged: false },
  { path: '.env.vault', status: 'untracked', staged: false }
];

export const INITIAL_AUTONOMY_TASKS: AutonomyTask[] = [
  {
    id: 'task-1',
    title: 'Vérifier la conformité des 42 pages de formation ATAM',
    priority: 'HIGH',
    status: 'in_progress',
    createdAt: '10:05',
    assignedAgent: 'antigravity',
    progressPercent: 70,
    logs: ['Extraction des tables DOCX...', 'Validation des 7 formateurs...', '0 page blanche confirmée.']
  },
  {
    id: 'task-2',
    title: 'Mettre à jour les dépendances de sécurité et masquer les secrets',
    priority: 'NORMAL',
    status: 'ready',
    createdAt: '09:40',
    assignedAgent: 'claude',
    progressPercent: 0,
    logs: ['En attente de démarrage']
  },
  {
    id: 'task-3',
    title: 'Générer le graphe Mermaid des dépendances du projet',
    priority: 'NORMAL',
    status: 'done',
    createdAt: '09:15',
    assignedAgent: 'opencode',
    progressPercent: 100,
    logs: ['AST parsing complet', 'Graphe de 24 modules exporté avec succès']
  },
  {
    id: 'task-4',
    title: 'Déployer la prévisualisation vers Cloudflare Pages Edge',
    priority: 'LOW',
    status: 'ready',
    createdAt: '08:50',
    assignedAgent: 'hermes',
    progressPercent: 0,
    logs: ['En attente de déclenchement']
  }
];

export const INITIAL_VAULT_SECRETS: VaultSecret[] = [
  {
    id: 'sec-1',
    key: 'GEMINI_API_KEY',
    value: 'AIzaSyA89v_kL791mN284OpQ0249xXbZ_912',
    provider: 'Gemini',
    masked: true,
    updatedAt: '2026-10-14'
  },
  {
    id: 'sec-2',
    key: 'ANTHROPIC_API_KEY',
    value: 'sk-ant-api03-91kdJa8712mZa09124_Lkj1',
    provider: 'Anthropic',
    masked: true,
    updatedAt: '2026-10-13'
  },
  {
    id: 'sec-3',
    key: 'CLOUDFLARE_API_TOKEN',
    value: 'cf_tok_81726a9b1c2014ff901234',
    provider: 'Cloudflare',
    masked: true,
    updatedAt: '2026-10-12'
  },
  {
    id: 'sec-4',
    key: 'GITHUB_PERSONAL_ACCESS_TOKEN',
    value: 'ghp_918237192837192837192837',
    provider: 'GitHub',
    masked: true,
    updatedAt: '2026-10-11'
  }
];

export const INITIAL_MEMORY_ITEMS: MemoryItem[] = [
  {
    id: 'mem-1',
    tier: 'procedural',
    title: 'Workflow Génération ATAM 42 Pages',
    content: 'Toujours compiler les 7 livrets formateurs avec scripts/build_module.py sans insérer de sauts de page vides.',
    tags: ['ATAM', 'DOCX', 'PDF', 'Réglementation'],
    accessCount: 42,
    createdAt: '2026-10-12',
    confidence: 0.98
  },
  {
    id: 'mem-2',
    tier: 'semantic',
    title: 'Contraintes Portables WinForms Bridge 8001',
    content: 'Le processus AgyStudioFolderPicker.exe écoute en HTTP REST sur 127.0.0.1:8001 pour ouvrir le sélecteur natif de dossiers Windows 11.',
    tags: ['Windows', 'C#', 'Port 8001', 'Picker'],
    accessCount: 19,
    createdAt: '2026-10-11',
    confidence: 0.95
  },
  {
    id: 'mem-3',
    tier: 'episodic',
    title: 'Correction de régression sur la vue Split Diff Monaco',
    content: 'Résolu l\'écrasement des tabs dans le visualisateur de diff en isolant l\'état local du modèle original.',
    tags: ['Monaco', 'Diff', 'Bugfix'],
    accessCount: 8,
    createdAt: '2026-10-13',
    confidence: 0.91
  }
];

export const INITIAL_MODELS: ModelOption[] = [
  {
    id: 'gemini-3.8-flash',
    name: 'Gemini 3.8 Flash',
    provider: 'Google DeepMind',
    contextWindow: '1M tokens',
    latency: '~120ms',
    description: 'Vitesse instantanée, idéal pour le Vibe Coding, l\'édition en direct et les flux réactifs.',
    badge: 'Recommandé',
    isDefault: true
  },
  {
    id: 'gemini-3.1-pro',
    name: 'Gemini 3.1 Pro',
    provider: 'Google DeepMind',
    contextWindow: '2M tokens',
    latency: '~380ms',
    description: 'Grandes capacités de raisonnement multimodal, documentation massive et refactorings complexes.',
    badge: 'Ultra Pro'
  },
  {
    id: 'claude-3.7-sonnet',
    name: 'Claude 3.7 Sonnet',
    provider: 'Anthropic',
    contextWindow: '200K tokens',
    latency: '~450ms',
    description: 'Spécialiste de l\'ingénierie logicielle haut niveau et des architectures multi-fichiers.',
    badge: 'Architecture'
  },
  {
    id: 'deepseek-v3',
    name: 'DeepSeek-V3 Coder',
    provider: 'DeepSeek',
    contextWindow: '128K tokens',
    latency: '~220ms',
    description: 'Excellente efficacité pour la synthèse d\'algorithmes et l\'écriture de tests unitaires.',
    badge: 'Coding'
  }
];

export const INITIAL_MCP_SERVERS: McpServer[] = [
  {
    id: 'mcp-wp',
    name: 'WordPress Engine (Vibecoding & Blog)',
    category: 'wordpress',
    status: 'connected',
    endpoint: 'http://localhost:8080/wp-json/mcp',
    tools: ['create_post', 'update_theme_block', 'audit_plugins', 'query_db']
  },
  {
    id: 'mcp-vps',
    name: 'VPS / SSH Cloud Instance',
    category: 'vps',
    status: 'connected',
    endpoint: 'ssh://root@192.168.1.50:22',
    tools: ['exec_cmd', 'docker_compose_up', 'read_syslog', 'restart_service']
  },
  {
    id: 'mcp-gh',
    name: 'GitHub Repository MCP Server',
    category: 'github',
    status: 'connected',
    endpoint: 'github-mcp://infohas-Rabat224/agy-studio',
    tools: ['create_pull_request', 'list_issues', 'dispatch_workflow']
  }
];

export const INITIAL_QUOTAS: QuotaMetric[] = [
  {
    name: 'Requêtes par Minute (RPM)',
    used: 18,
    limit: 300,
    unit: 'req/min',
    percent: 6,
    resetIn: '42s'
  },
  {
    name: 'Tokens par Minute (TPM)',
    used: 48500,
    limit: 1000000,
    unit: 'tokens/min',
    percent: 4.8,
    resetIn: '42s'
  },
  {
    name: 'Requêtes Journalières (RPD)',
    used: 1240,
    limit: 10000,
    unit: 'req/jour',
    percent: 12.4,
    resetIn: '13h 40m'
  }
];

export const INITIAL_TIMEMACHINE_SNAPSHOTS: TimeMachineSnapshot[] = [
  {
    id: 'snap-3',
    timestamp: '10:14:22',
    prompt: 'Mettre à jour le header avec 5 sélecteurs compacts et status bar',
    agent: 'antigravity',
    filesChanged: ['src/components/Header.tsx', 'src/components/StatusBar.tsx'],
    diffSummary: '+142 lines, -38 lines across 2 files'
  },
  {
    id: 'snap-2',
    timestamp: '09:52:10',
    prompt: 'Ajouter les modèles de serveurs MCP WordPress et VPS',
    agent: 'hermes',
    filesChanged: ['backend/mcp/connectors.py', 'src/data/initialData.ts'],
    diffSummary: '+88 lines, -12 lines'
  },
  {
    id: 'snap-1',
    timestamp: '09:20:05',
    prompt: 'Initialisation du catalogue de mémoire adaptative à 3 niveaux',
    agent: 'claude',
    filesChanged: ['backend/memory/memory_manager.py'],
    diffSummary: '+310 lines, initial commit'
  }
];
