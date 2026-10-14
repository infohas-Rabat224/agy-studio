import React, { useState } from 'react';
import {
  FolderTree,
  PanelLeftClose,
  Folder,
  FileCode,
  FileText,
  FileCheck,
  Trash2,
  Sparkles,
  Zap,
  CheckCircle2,
  GraduationCap,
  ListTodo,
  Layers
} from 'lucide-react';
import { useStudio } from '../context/StudioContext';
import { WorkspaceFile } from '../types';

export const LeftSidebar: React.FC = () => {
  const {
    isSidebarOpen,
    setIsSidebarOpen,
    currentMode,
    files,
    openFileInPreview,
    sendMessage,
    matrixLogs,
    clearMatrixLogs,
    openModal
  } = useStudio();

  const [injectedFiles, setInjectedFiles] = useState<string[]>(['backend/server.py']);

  if (!isSidebarOpen) {
    return (
      <div className="w-8 border-r border-slate-800/80 bg-slate-950/90 flex flex-col items-center py-2 flex-shrink-0 z-10 select-none">
        <button
          onClick={() => setIsSidebarOpen(true)}
          title="Déplier le panneau d'outils et de fichiers (Ctrl+B)"
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition mb-3 cursor-pointer"
        >
          <FolderTree className="w-4 h-4 text-sky-400" />
        </button>
        <div className="writing-vertical text-[10px] uppercase font-mono text-slate-500 tracking-wider rotate-180">
          Outils & Fichiers
        </div>
      </div>
    );
  }

  const toggleInjectFile = (path: string) => {
    setInjectedFiles(prev =>
      prev.includes(path) ? prev.filter(p => p !== path) : [...prev, path]
    );
  };

  return (
    <aside className="w-80 border-r border-slate-800/80 bg-slate-950/70 flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out select-none">
      {/* Sidebar Header */}
      <div className="h-8 px-2.5 bg-slate-900/60 border-b border-slate-800/60 flex items-center justify-between text-xs flex-shrink-0">
        <span className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
          <FolderTree className="w-3.5 h-3.5 text-sky-400" />
          <span>Outils & Fichiers</span>
        </span>
        <button
          onClick={() => setIsSidebarOpen(false)}
          title="Replier le panneau latéral (Ctrl+B)"
          className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition cursor-pointer"
        >
          <PanelLeftClose className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Dynamic Mode Sidebar Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* Mode Specific Card */}
        <div className="p-2.5 bg-slate-900/80 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-slate-200">
            <span className="flex items-center gap-1.5 text-sky-400">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Actions du Mode Actif</span>
            </span>
            <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-sky-950 text-sky-300 font-mono">
              {currentMode.replace('_', ' ')}
            </span>
          </div>

          <div className="grid grid-cols-1 gap-1 text-[11px]">
            {currentMode === 'vibe_coding' && (
              <>
                <button
                  onClick={() => sendMessage('Génère un composant réactif moderne avec Tailwind CSS')}
                  className="px-2 py-1 text-left bg-slate-950/60 hover:bg-slate-800 text-slate-300 rounded border border-slate-800/80 flex items-center gap-1.5 cursor-pointer"
                >
                  <Zap className="w-3 h-3 text-amber-400" /> Nouveau Composant React
                </button>
                <button
                  onClick={() => openModal('monaco')}
                  className="px-2 py-1 text-left bg-slate-950/60 hover:bg-slate-800 text-slate-300 rounded border border-slate-800/80 flex items-center gap-1.5 cursor-pointer"
                >
                  <FileCode className="w-3 h-3 text-sky-400" /> Inspecter Diff & Monaco
                </button>
              </>
            )}

            {currentMode === 'pedagogie' && (
              <>
                <button
                  onClick={() => sendMessage('Vérifie les 42 pages de formation des 7 formateurs ATAM')}
                  className="px-2 py-1 text-left bg-slate-950/60 hover:bg-slate-800 text-amber-300 rounded border border-amber-900/40 flex items-center gap-1.5 cursor-pointer"
                >
                  <GraduationCap className="w-3 h-3 text-amber-400" /> Valider les 7 Formateurs
                </button>
                <button
                  onClick={() => openModal('visionReflex')}
                  className="px-2 py-1 text-left bg-slate-950/60 hover:bg-slate-800 text-slate-300 rounded border border-slate-800/80 flex items-center gap-1.5 cursor-pointer"
                >
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Audit Conformité PDF
                </button>
              </>
            )}

            {currentMode === 'tasks' && (
              <>
                <button
                  onClick={() => openModal('autonomy')}
                  className="px-2 py-1 text-left bg-slate-950/60 hover:bg-slate-800 text-emerald-300 rounded border border-emerald-900/40 flex items-center gap-1.5 cursor-pointer"
                >
                  <ListTodo className="w-3 h-3 text-emerald-400" /> Ouvrir File d'Attente
                </button>
                <button
                  onClick={() => sendMessage('Lance les tâches autonomes de fond et déclenche les notifications Windows 11')}
                  className="px-2 py-1 text-left bg-slate-950/60 hover:bg-slate-800 text-slate-300 rounded border border-slate-800/80 flex items-center gap-1.5 cursor-pointer"
                >
                  <Zap className="w-3 h-3 text-amber-400" /> Exécuter Ghost Mode
                </button>
              </>
            )}

            {currentMode === 'deep_thinking' && (
              <>
                <button
                  onClick={() => sendMessage('/boost Analyse en profondeur l\'architecture système et le graphe de dépendances')}
                  className="px-2 py-1 text-left bg-slate-950/60 hover:bg-slate-800 text-indigo-300 rounded border border-indigo-900/40 flex items-center gap-1.5 cursor-pointer"
                >
                  <Zap className="w-3 h-3 text-indigo-400" /> Raisonnement Profond (/boost)
                </button>
                <button
                  onClick={() => openModal('projectGraph')}
                  className="px-2 py-1 text-left bg-slate-950/60 hover:bg-slate-800 text-slate-300 rounded border border-slate-800/80 flex items-center gap-1.5 cursor-pointer"
                >
                  <Layers className="w-3 h-3 text-purple-400" /> Cartographie des Modules
                </button>
              </>
            )}

            {currentMode === 'creative' && (
              <>
                <button
                  onClick={() => sendMessage('Génère un storyboard infographique moderne avec mise en page Bento')}
                  className="px-2 py-1 text-left bg-slate-950/60 hover:bg-slate-800 text-purple-300 rounded border border-purple-900/40 flex items-center gap-1.5 cursor-pointer"
                >
                  <Sparkles className="w-3 h-3 text-purple-400" /> Créer Infographie Bento
                </button>
              </>
            )}
          </div>
        </div>

        {/* Mini File Manager */}
        <div className="bg-slate-900/50 border border-slate-800 p-2.5 rounded-xl">
          <div className="font-bold text-xs text-slate-300 mb-2 flex justify-between items-center">
            <span className="flex items-center gap-1.5">
              <Folder className="w-3.5 h-3.5 text-amber-400" />
              <span>Explorateur de Fichiers</span>
            </span>
            <span className="text-[10px] font-mono text-slate-500">{files.length} fichiers</span>
          </div>

          <div className="space-y-1 max-h-36 overflow-y-auto text-xs text-slate-300 pr-1">
            {files.map(f => (
              <div
                key={f.path}
                onClick={() => openFileInPreview(f)}
                className="px-2 py-1 bg-slate-950/60 hover:bg-slate-800/80 rounded border border-slate-800/60 flex items-center justify-between cursor-pointer transition"
              >
                <span className="truncate flex items-center gap-1.5 text-[11px]">
                  {f.name.endsWith('.py') ? (
                    <FileCode className="w-3 h-3 text-sky-400 flex-shrink-0" />
                  ) : (
                    <FileText className="w-3 h-3 text-amber-400 flex-shrink-0" />
                  )}
                  <span className="truncate">{f.name}</span>
                </span>
                <span className="text-[9px] font-mono text-slate-500">
                  {f.size ? `${(f.size / 1024).toFixed(0)}k` : ''}
                </span>
              </div>
            ))}
          </div>

          {/* Context File Injector */}
          <div className="font-bold text-xs text-slate-300 mt-4 mb-2 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Context Injector</span>
            </span>
            <span className="text-[10px] font-mono text-emerald-400">
              {injectedFiles.length} actifs
            </span>
          </div>

          <div className="space-y-1 max-h-28 overflow-y-auto text-xs text-slate-400 pr-1">
            {files.map(f => (
              <label
                key={f.path}
                className="flex items-center gap-2 px-2 py-1 bg-slate-950/40 hover:bg-slate-800/60 rounded border border-slate-800/40 cursor-pointer text-[11px]"
              >
                <input
                  type="checkbox"
                  checked={injectedFiles.includes(f.path)}
                  onChange={() => toggleInjectFile(f.path)}
                  className="rounded border-slate-700 text-sky-500 focus:ring-0"
                />
                <span className="truncate text-slate-300">{f.name}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* MATRIX LIVE KERNEL TERMINAL (LOWER LEFT) */}
      <div className="h-56 border-t border-emerald-900/50 bg-[#020508] flex flex-col flex-shrink-0 font-mono text-[10px] shadow-2xl relative">
        {/* Terminal Header */}
        <div className="h-7 px-2.5 bg-[#03080e] border-b border-emerald-900/40 flex items-center justify-between text-emerald-400 select-none">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-extrabold tracking-wider text-[9px] uppercase text-emerald-400">
              // MATRIX LIVE STREAM
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[8px] font-bold px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
              IDLE
            </span>
            <button
              onClick={clearMatrixLogs}
              title="Effacer la console"
              className="text-emerald-600 hover:text-emerald-300 px-1 cursor-pointer"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Terminal Output Screen */}
        <div className="flex-1 p-2 overflow-y-auto text-[#00ff66] leading-snug space-y-0.5 select-text font-mono text-[10px]">
          {matrixLogs.map((log, i) => (
            <div key={i} className="whitespace-pre-wrap">{log}</div>
          ))}
        </div>
      </div>
    </aside>
  );
};
