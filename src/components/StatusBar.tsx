import React from 'react';
import { Terminal, GitBranch, ListTodo, Code2, FileText } from 'lucide-react';
import { useStudio } from '../context/StudioContext';

export const StatusBar: React.FC = () => {
  const {
    workspacePath,
    isTerminalOpen,
    setIsTerminalOpen,
    openModal,
    isPreviewOpen,
    setIsPreviewOpen,
    quotas,
    autonomyTasks
  } = useStudio();

  const activeTasksCount = autonomyTasks.filter(t => t.status === 'in_progress' || t.status === 'ready').length;

  return (
    <footer className="h-6 border-t border-slate-800 bg-[#070b14] px-3 flex items-center justify-between text-[10px] text-slate-400 select-none z-20 flex-shrink-0 font-mono">
      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
        <span className="flex items-center gap-1.5 flex-shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          <span className="text-slate-300 font-semibold truncate max-w-[140px] sm:max-w-xs">
            {workspacePath.split('\\').pop() || 'gemini-projects'}
          </span>
        </span>
        <span className="text-slate-700">•</span>
        <button
          onClick={() => setIsTerminalOpen(!isTerminalOpen)}
          className="text-emerald-400 font-semibold cursor-pointer hover:underline flex items-center gap-1"
          title="Ouvrir le terminal (Ctrl+`)"
        >
          <Terminal className="w-3 h-3" />
          <span>Terminal (Ctrl+`)</span>
        </button>
        <span className="text-slate-700">•</span>
        <button
          onClick={() => openModal('git')}
          className="text-purple-400 font-semibold cursor-pointer hover:underline flex items-center gap-1"
          title="Ouvrir Git GUI"
        >
          <GitBranch className="w-3 h-3" />
          <span>Git GUI</span>
        </button>
        <span className="text-slate-700">•</span>
        <button
          onClick={() => openModal('autonomy')}
          className="text-amber-400 font-semibold cursor-pointer hover:underline flex items-center gap-1"
          title="Ouvrir la file d'autonomie"
        >
          <ListTodo className="w-3 h-3" />
          <span>Autonomie ({activeTasksCount})</span>
        </button>
        <span className="text-slate-700">•</span>
        <button
          onClick={() => openModal('monaco')}
          className="text-sky-400 font-semibold cursor-pointer hover:underline flex items-center gap-1"
          title="Ouvrir l'éditeur Monaco"
        >
          <Code2 className="w-3 h-3" />
          <span>Monaco & Diff</span>
        </button>
        <span className="text-slate-700">•</span>
        <button
          onClick={() => setIsPreviewOpen(!isPreviewOpen)}
          className="text-indigo-400 font-semibold cursor-pointer hover:underline flex items-center gap-1"
          title="Basculer le volet d'aperçu d'artefact"
        >
          <FileText className="w-3 h-3" />
          <span>Aperçu</span>
        </button>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          onClick={() => openModal('intelligence')}
          className="text-indigo-400 cursor-pointer hover:underline font-semibold flex items-center gap-1"
        >
          <span>✦ Learning: Active</span>
        </button>
        <span className="text-slate-700">•</span>
        <span className="text-emerald-400 font-semibold">Pont 8001: Prêt</span>
        <span className="text-slate-700">•</span>
        <button
          onClick={() => openModal('quota')}
          className="text-slate-400 cursor-pointer hover:underline"
        >
          Quota: {quotas[0]?.percent ?? 6}%
        </button>
      </div>
    </footer>
  );
};
