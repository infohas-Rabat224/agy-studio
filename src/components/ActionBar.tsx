import React, { useState, useRef, useEffect } from 'react';
import {
  PanelLeft,
  Plus,
  Search,
  Folder,
  Database,
  ListChecks,
  CheckCircle,
  PanelRight,
  Code2,
  Terminal,
  GitBranch,
  Swords,
  FileText,
  Eye,
  ShieldAlert,
  ListTodo,
  Network,
  Key,
  Cloud,
  Kanban,
  History,
  ChevronDown,
  Zap,
  Bot,
  Gauge,
  Download,
  BarChart2,
  Globe,
  HelpCircle
} from 'lucide-react';
import { useStudio } from '../context/StudioContext';

export const ActionBar: React.FC = () => {
  const {
    isSidebarOpen,
    setIsSidebarOpen,
    isPreviewOpen,
    setIsPreviewOpen,
    isTerminalOpen,
    setIsTerminalOpen,
    createSession,
    openModal,
    sendMessage,
    currentModel,
    quotas
  } = useStudio();

  const [moreDropdown, setMoreDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setMoreDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="h-9 border-b border-slate-800/80 bg-slate-950/90 px-3 flex items-center justify-between gap-2 flex-shrink-0 z-20 text-xs select-none">
      <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5">
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className={`px-2 py-0.5 rounded text-[11px] border flex items-center gap-1 transition cursor-pointer ${
            isSidebarOpen ? 'bg-slate-800 border-sky-500/50 text-sky-400' : 'bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-300'
          }`}
          title="Afficher / Masquer le volet gauche (Ctrl+B)"
        >
          <PanelLeft className="w-3 h-3 text-sky-400" />
          <span>Panneau</span>
        </button>

        <button
          onClick={() => createSession()}
          className="px-2.5 py-0.5 bg-emerald-600/90 hover:bg-emerald-500 text-white rounded text-[11px] font-semibold flex items-center gap-1 transition shadow cursor-pointer"
        >
          <Plus className="w-3 h-3" />
          <span>Session</span>
        </button>

        <button
          onClick={() => openModal('commandPalette')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded text-[11px] border border-slate-800 flex items-center gap-1 transition cursor-pointer"
        >
          <Search className="w-3 h-3 text-sky-400" />
          <span>Recherche</span>
        </button>

        <button
          onClick={() => openModal('memory')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded text-[11px] border border-slate-800 flex items-center gap-1 transition cursor-pointer"
        >
          <Database className="w-3 h-3 text-rose-400" />
          <span>Mémoire</span>
        </button>

        <button
          onClick={() => sendMessage('/plan ')}
          className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-sky-400 font-mono rounded text-[11px] border border-slate-700 flex items-center gap-1 transition cursor-pointer"
        >
          <ListChecks className="w-3 h-3" />
          <span>Plan</span>
        </button>

        <button
          onClick={() => openModal('intelligence')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-emerald-400 font-medium rounded text-[11px] border border-slate-800 flex items-center gap-1 transition cursor-pointer"
        >
          <CheckCircle className="w-3 h-3" />
          <span>Vérifier</span>
        </button>

        <button
          onClick={() => setIsPreviewOpen(!isPreviewOpen)}
          className={`px-2 py-0.5 rounded text-[11px] border flex items-center gap-1 transition cursor-pointer ${
            isPreviewOpen ? 'bg-slate-800 border-indigo-500/50 text-indigo-300' : 'bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-300'
          }`}
          title="Afficher / Masquer l'aperçu (Ctrl+J)"
        >
          <PanelRight className="w-3 h-3 text-indigo-400" />
          <span>Aperçu</span>
        </button>

        <button
          onClick={() => openModal('monaco')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-sky-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-sky-500/50 flex items-center gap-1 transition cursor-pointer"
          title="Éditeur Monaco & Split Diff View"
        >
          <Code2 className="w-3 h-3 text-sky-400" />
          <span>Code & Diff</span>
        </button>

        <button
          onClick={() => setIsTerminalOpen(!isTerminalOpen)}
          className={`px-2 py-0.5 rounded text-[11px] border flex items-center gap-1 transition cursor-pointer ${
            isTerminalOpen ? 'bg-emerald-950/60 border-emerald-500 text-emerald-300' : 'bg-slate-900 hover:bg-slate-800 border-slate-800 text-emerald-400'
          }`}
          title="Terminal Interactif (PowerShell) (Ctrl+`)"
        >
          <Terminal className="w-3 h-3 text-emerald-400" />
          <span>Terminal</span>
        </button>

        <button
          onClick={() => openModal('git')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-purple-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-purple-500/50 flex items-center gap-1 transition cursor-pointer"
          title="Contrôle de Version Git & GitHub Timeline"
        >
          <GitBranch className="w-3 h-3 text-purple-400" />
          <span>Git GUI</span>
        </button>

        <button
          onClick={() => openModal('agentDuel')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-sky-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-sky-500/50 flex items-center gap-1 transition cursor-pointer"
          title="Arène & Duel Comparatif Multi-Agents"
        >
          <Swords className="w-3 h-3 text-sky-400" />
          <span>Duel Multi-Agents</span>
        </button>

        <button
          onClick={() => openModal('sessionReport')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-indigo-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-indigo-500/50 flex items-center gap-1 transition cursor-pointer"
          title="Générateur de Rapport de Session & Pull Request GitHub"
        >
          <FileText className="w-3 h-3 text-indigo-400" />
          <span>Rapport & PR</span>
        </button>

        <button
          onClick={() => openModal('autonomy')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-amber-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-amber-500/50 flex items-center gap-1 transition cursor-pointer"
          title="File d'Attente d'Autonomie (Ghost Mode & Windows Toasts)"
        >
          <ListTodo className="w-3 h-3 text-amber-400" />
          <span>Autonomie</span>
        </button>

        <button
          onClick={() => openModal('projectGraph')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-indigo-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-indigo-500/50 flex items-center gap-1 transition cursor-pointer"
          title="Cartographie Visuelle du Projet & Graphe des Dépendances"
        >
          <Network className="w-3 h-3 text-indigo-400" />
          <span>Graphe</span>
        </button>

        <button
          onClick={() => openModal('vault')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-rose-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-rose-500/50 flex items-center gap-1 transition cursor-pointer"
          title="Coffre-fort de Clés & Variables (.env Vault)"
        >
          <Key className="w-3 h-3 text-rose-400" />
          <span>Vault</span>
        </button>

        <button
          onClick={() => openModal('deploy')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-teal-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-teal-500/50 flex items-center gap-1 transition cursor-pointer"
          title="Déploiement Cloud 1-Clic"
        >
          <Cloud className="w-3 h-3 text-teal-400" />
          <span>Déployer</span>
        </button>

        <button
          onClick={() => openModal('visionReflex')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-pink-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-pink-500/50 flex items-center gap-1 transition cursor-pointer"
          title="Vision Reflex & Playwright"
        >
          <Eye className="w-3 h-3 text-pink-400" />
          <span>Reflex</span>
        </button>

        <button
          onClick={() => openModal('kanban')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-cyan-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-cyan-500/50 flex items-center gap-1 transition cursor-pointer"
          title="Tableau Kanban Visuel & Orchestration Multi-Agents"
        >
          <Kanban className="w-3 h-3 text-cyan-400" />
          <span>Kanban</span>
        </button>

        <button
          onClick={() => openModal('timeMachine')}
          className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-amber-400 font-semibold rounded text-[11px] border border-slate-800 hover:border-amber-500/50 flex items-center gap-1 transition cursor-pointer"
          title="Time-Machine Rollback"
        >
          <History className="w-3 h-3 text-amber-400" />
          <span>Rollback</span>
        </button>

        {/* More Actions Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setMoreDropdown(!moreDropdown)}
            className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded text-[11px] border border-slate-800 flex items-center gap-1 transition font-medium cursor-pointer"
          >
            <span>Plus</span> <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {moreDropdown && (
            <div className="absolute left-0 mt-1 w-56 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1.5 z-50 text-xs space-y-0.5">
              <button
                onClick={() => {
                  sendMessage('/boost ');
                  setMoreDropdown(false);
                }}
                className="w-full px-3 py-1.5 text-left text-indigo-300 hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <Zap className="w-3.5 h-3.5 text-indigo-400" /> Raisonnement approfondi (/boost)
              </button>
              <button
                onClick={() => {
                  openModal('model');
                  setMoreDropdown(false);
                }}
                className="w-full px-3 py-1.5 text-left text-sky-300 hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <Bot className="w-3.5 h-3.5 text-sky-400" /> Changer de modèle (/model)
              </button>
              <button
                onClick={() => {
                  openModal('mcp');
                  setMoreDropdown(false);
                }}
                className="w-full px-3 py-1.5 text-left text-purple-300 hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <Network className="w-3.5 h-3.5 text-purple-400" /> Serveurs MCP (/mcp)
              </button>
              <button
                onClick={() => {
                  openModal('quota');
                  setMoreDropdown(false);
                }}
                className="w-full px-3 py-1.5 text-left text-emerald-300 hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <Gauge className="w-3.5 h-3.5 text-emerald-400" /> Quotas réels (/quota)
              </button>
              <div className="border-t border-slate-800 my-1"></div>
              <button
                onClick={() => {
                  openModal('shortcuts');
                  setMoreDropdown(false);
                }}
                className="w-full px-3 py-1.5 text-left text-slate-400 hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <HelpCircle className="w-3.5 h-3.5 text-slate-400" /> Raccourcis clavier (?)
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Right: Environment & Quota indicator */}
      <div className="hidden sm:flex items-center gap-2 text-[10px] text-slate-400 flex-shrink-0">
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-mono text-slate-400">Antigravity CLI</span>
        </span>
        <span>•</span>
        <span
          onClick={() => openModal('quota')}
          className="font-mono text-emerald-400 cursor-pointer hover:underline"
        >
          Quota: {quotas[0]?.percent ?? 6}% RPM
        </span>
      </div>
    </div>
  );
};
