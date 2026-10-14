import React, { useState, useRef, useEffect } from 'react';
import {
  Cpu,
  Folder,
  ChevronDown,
  FolderSearch,
  Edit3,
  Code,
  Brain,
  GraduationCap,
  Sparkles,
  ListTodo,
  Bot,
  Check,
  Terminal,
  Code2,
  Layers,
  PlusCircle,
  List,
  Edit,
  Pin,
  Star,
  GitBranch,
  Search,
  Settings,
  Compass,
  TrendingUp,
  ShieldAlert,
  Database
} from 'lucide-react';
import { useStudio } from '../context/StudioContext';
import { StudioMode, AgentType } from '../types';

export const Header: React.FC = () => {
  const {
    currentMode,
    setCurrentMode,
    currentAgent,
    setCurrentAgent,
    agents,
    currentModel,
    workspacePath,
    setWorkspacePath,
    sessions,
    activeSession,
    createSession,
    togglePinSession,
    toggleFavoriteSession,
    renameSession,
    forkSession,
    openModal,
    language,
    setLanguage
  } = useStudio();

  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdown(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleDropdown = (name: string) => {
    setOpenDropdown(prev => (prev === name ? null : name));
  };

  const closeDropdown = () => setOpenDropdown(null);

  const getModeInfo = (mode: StudioMode) => {
    switch (mode) {
      case 'vibe_coding':
        return { label: 'Vibe Coding', icon: <Code className="w-3.5 h-3.5 text-sky-400" /> };
      case 'deep_thinking':
        return { label: 'Deep Thinking', icon: <Brain className="w-3.5 h-3.5 text-indigo-400" /> };
      case 'pedagogie':
        return { label: 'Pédagogie (ATAM)', icon: <GraduationCap className="w-3.5 h-3.5 text-amber-400" /> };
      case 'creative':
        return { label: 'Studio Média', icon: <Sparkles className="w-3.5 h-3.5 text-purple-400" /> };
      case 'tasks':
        return { label: 'Autonomie', icon: <ListTodo className="w-3.5 h-3.5 text-emerald-400" /> };
    }
  };

  const currentModeInfo = getModeInfo(currentMode);

  return (
    <header
      ref={dropdownRef}
      className="h-12 border-b border-slate-800 bg-[#0c1222]/95 px-3 flex items-center justify-between gap-2 flex-shrink-0 z-40 backdrop-blur min-w-0 select-none"
    >
      {/* Left: Brand & Version */}
      <div className="flex items-center space-x-2 flex-shrink-0">
        <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-sky-500 via-indigo-500 to-fuchsia-500 p-0.5 shadow-md flex-shrink-0">
          <div className="w-full h-full bg-slate-950 rounded-[6px] flex items-center justify-center">
            <Cpu className="w-3.5 h-3.5 text-sky-400" />
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <h1 className="font-bold text-xs sm:text-sm tracking-wide bg-gradient-to-r from-sky-400 to-indigo-300 bg-clip-text text-transparent whitespace-nowrap">
            AGY STUDIO
          </h1>
          <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-sky-950 border border-sky-800 text-sky-400 font-bold">
            v2.6
          </span>
        </div>
      </div>

      {/* Center/Right: 5 Compact Selectors + Settings */}
      <div className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
        {/* 1. WORKSPACE SELECTOR */}
        <div className="relative">
          <button
            onClick={() => toggleDropdown('ws')}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/50 rounded-lg text-xs font-medium text-slate-200 transition shadow-inner cursor-pointer"
          >
            <Folder className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <span className="max-w-[85px] sm:max-w-[120px] md:max-w-[150px] truncate font-mono text-[11px]">
              {workspacePath.split('\\').pop() || 'workspace'}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400 flex-shrink-0" />
          </button>

          {openDropdown === 'ws' && (
            <div className="absolute left-0 mt-1 w-64 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1.5 z-50 text-xs space-y-1">
              <div className="px-3 py-1 text-[10px] text-slate-500 font-semibold uppercase">Espace de Travail</div>
              <button
                onClick={() => {
                  const p = prompt('Sélectionnez ou saisissez le chemin de votre espace :', workspacePath);
                  if (p) setWorkspacePath(p);
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <FolderSearch className="w-3.5 h-3.5 text-amber-400" /> Parcourir (Sélecteur Windows Natif)
              </button>
              <button
                onClick={() => {
                  const p = prompt('Saisissez le chemin absolu du répertoire :', workspacePath);
                  if (p) setWorkspacePath(p);
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <Edit3 className="w-3.5 h-3.5 text-sky-400" /> Saisir chemin absolu...
              </button>
              <div className="border-t border-slate-800/80 my-1"></div>
              <div className="px-3 py-1 text-[10px] text-slate-400 flex items-center justify-between">
                <span>Pont Natif (8001) :</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1 font-semibold">● Prêt</span>
              </div>
            </div>
          )}
        </div>

        {/* 2. MODE SELECTOR */}
        <div className="relative">
          <button
            onClick={() => toggleDropdown('mode')}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-sky-500/50 rounded-lg text-xs font-semibold text-slate-200 transition shadow-inner cursor-pointer"
          >
            {currentModeInfo.icon}
            <span className="text-slate-200 hidden xs:inline">{currentModeInfo.label}</span>
            <ChevronDown className="w-3 h-3 text-slate-400 flex-shrink-0" />
          </button>

          {openDropdown === 'mode' && (
            <div className="absolute left-0 mt-1 w-52 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1.5 z-50 text-xs space-y-0.5">
              <div className="px-3 py-1 text-[10px] text-slate-500 font-semibold uppercase">Mode Actif</div>
              {(['vibe_coding', 'deep_thinking', 'pedagogie', 'creative', 'tasks'] as StudioMode[]).map(m => {
                const info = getModeInfo(m);
                return (
                  <button
                    key={m}
                    onClick={() => {
                      setCurrentMode(m);
                      closeDropdown();
                    }}
                    className={`w-full px-3 py-1.5 text-left flex items-center gap-2 cursor-pointer transition ${
                      currentMode === m ? 'bg-slate-800 text-sky-400 font-semibold' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`}
                  >
                    {info.icon}
                    <span>{info.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* 3. INTELLIGENCE (Compact status pill & dropdown) */}
        <div className="relative">
          <button
            onClick={() => toggleDropdown('intel')}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-indigo-950/40 hover:bg-indigo-900/60 border border-indigo-700/50 hover:border-indigo-500 rounded-lg text-xs font-semibold text-indigo-200 transition shadow-inner cursor-pointer"
          >
            <span className="text-indigo-400 font-bold">✦</span>
            <span className="text-indigo-300 font-medium hidden sm:inline">✦ Learning Active</span>
            <ChevronDown className="w-3 h-3 text-indigo-400 flex-shrink-0" />
          </button>

          {openDropdown === 'intel' && (
            <div className="absolute left-0 mt-1 w-64 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1.5 z-50 text-xs space-y-0.5">
              <div className="px-3 py-1 text-[10px] text-slate-500 font-semibold uppercase">Intelligence Adaptative</div>
              <button
                onClick={() => {
                  openModal('intelligence');
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-indigo-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 font-medium cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Dashboard Intelligence v2.6
              </button>
              <button
                onClick={() => {
                  openModal('memory');
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <Database className="w-3.5 h-3.5 text-rose-400" /> Catalogue Mémoire (3-Tier)
              </button>
              <button
                onClick={() => {
                  openModal('intelligence');
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <Compass className="w-3.5 h-3.5 text-sky-400" /> Stratégies Apprises (42)
              </button>
              <button
                onClick={() => {
                  openModal('intelligence');
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Performance Agents (96.4%)
              </button>
              <button
                onClick={() => {
                  openModal('intelligence');
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" /> Risques & Régressions (0 Détecté)
              </button>
            </div>
          )}
        </div>

        {/* 4. AGENT SELECTOR */}
        <div className="relative">
          <button
            onClick={() => toggleDropdown('agent')}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-sky-500/50 rounded-lg text-xs font-semibold text-slate-200 transition shadow-inner cursor-pointer"
          >
            <Bot className="w-3.5 h-3.5 text-sky-400 flex-shrink-0" />
            <span className="text-sky-300 hidden sm:inline">
              {agents.find(a => a.id === currentAgent)?.name.split(' ')[0] || 'Antigravity'}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400 flex-shrink-0" />
          </button>

          {openDropdown === 'agent' && (
            <div className="absolute right-0 mt-1 w-64 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1.5 z-50 text-xs space-y-0.5">
              <div className="px-3 py-1 text-[10px] text-slate-500 font-semibold uppercase">Orchestrateur & Agents</div>
              {agents.map(a => (
                <button
                  key={a.id}
                  onClick={() => {
                    setCurrentAgent(a.id);
                    closeDropdown();
                  }}
                  className="w-full px-3 py-1.5 text-left text-slate-200 hover:bg-slate-800 flex items-center justify-between cursor-pointer"
                >
                  <span className="flex items-center gap-2">
                    {currentAgent === a.id ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Terminal className="w-3.5 h-3.5 text-slate-500" />
                    )}
                    <span className={currentAgent === a.id ? 'font-bold text-white' : 'text-slate-300'}>{a.name}</span>
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400">{a.status}</span>
                </button>
              ))}
              <div className="border-t border-slate-800/80 my-1"></div>
              <button
                onClick={() => {
                  openModal('model');
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-sky-400 hover:bg-slate-800 flex items-center gap-2 font-medium cursor-pointer"
              >
                <Cpu className="w-3.5 h-3.5" /> Modèle : <span className="font-mono text-slate-300">{currentModel}</span>
              </button>
            </div>
          )}
        </div>

        {/* 5. SESSION SELECTOR */}
        <div className="relative">
          <button
            onClick={() => toggleDropdown('session')}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-indigo-950/30 hover:bg-indigo-900/50 border border-indigo-800/60 rounded-lg text-xs font-semibold text-indigo-300 transition shadow-inner cursor-pointer"
          >
            <Layers className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
            <span className="max-w-[80px] sm:max-w-[110px] md:max-w-[140px] truncate">
              {activeSession.title}
            </span>
            <ChevronDown className="w-3 h-3 text-indigo-400 flex-shrink-0" />
          </button>

          {openDropdown === 'session' && (
            <div className="absolute right-0 mt-1 w-64 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1.5 z-50 text-xs space-y-0.5">
              <div className="px-3 py-1 text-[10px] text-slate-500 font-semibold uppercase">Sessions Persistantes</div>
              <button
                onClick={() => {
                  createSession();
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-emerald-400 hover:bg-slate-800 flex items-center gap-2 font-semibold cursor-pointer"
              >
                <PlusCircle className="w-3.5 h-3.5" /> Nouvelle Session
              </button>
              <button
                onClick={() => {
                  openModal('session');
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <List className="w-3.5 h-3.5 text-indigo-400" /> Explorer toutes les sessions ({sessions.length})
              </button>
              <button
                onClick={() => {
                  const title = prompt('Renommer la session active :', activeSession.title);
                  if (title) renameSession(activeSession.id, title);
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <Edit className="w-3.5 h-3.5 text-sky-400" /> Renommer session active
              </button>
              <button
                onClick={() => {
                  togglePinSession(activeSession.id);
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <Pin className={`w-3.5 h-3.5 ${activeSession.pinned ? 'text-amber-400' : 'text-slate-400'}`} />
                {activeSession.pinned ? 'Désépingler' : 'Épingler 📌'}
              </button>
              <button
                onClick={() => {
                  toggleFavoriteSession(activeSession.id);
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <Star className={`w-3.5 h-3.5 ${activeSession.favorite ? 'text-amber-400 fill-amber-400' : 'text-slate-400'}`} />
                {activeSession.favorite ? 'Retirer des Favoris' : 'Marquer Favori ⭐'}
              </button>
              <button
                onClick={() => {
                  forkSession(activeSession.id);
                  closeDropdown();
                }}
                className="w-full px-3 py-1.5 text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-2 cursor-pointer"
              >
                <GitBranch className="w-3.5 h-3.5 text-purple-400" /> Forker cette session (Branche)
              </button>
            </div>
          )}
        </div>

        {/* COMMAND PALETTE TRIGGER (Ctrl+K) */}
        <button
          onClick={() => openModal('commandPalette')}
          title="Ouvrir la palette de commandes (Ctrl+K)"
          className="hidden md:flex items-center gap-1 px-2 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 rounded-lg text-xs font-mono transition cursor-pointer"
        >
          <Search className="w-3.5 h-3.5" />
          <kbd className="text-[10px] bg-slate-800 px-1 py-0.5 rounded text-slate-400">Ctrl K</kbd>
        </button>

        {/* LANGUAGE SWITCHER (FR / EN) */}
        <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs font-bold shadow-inner">
          <button
            onClick={() => setLanguage('fr')}
            className={`px-2 py-0.5 rounded text-[11px] transition font-semibold cursor-pointer ${
              language === 'fr' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            FR
          </button>
          <button
            onClick={() => setLanguage('en')}
            className={`px-2 py-0.5 rounded text-[11px] transition font-semibold cursor-pointer ${
              language === 'en' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            EN
          </button>
        </div>

        {/* 6. SETTINGS */}
        <button
          onClick={() => openModal('settings')}
          title="Paramètres Généraux & Intelligence"
          className="p-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white rounded-lg transition cursor-pointer"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
