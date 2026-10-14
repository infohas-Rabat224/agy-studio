import React, { useState } from 'react';
import { GitBranch, ArrowDown, ArrowUp, RotateCw, X, FileDiff, Sparkles, Check, GitCommit } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const GitModal: React.FC = () => {
  const {
    activeModal,
    closeModal,
    gitCommits,
    gitFiles,
    gitBranch,
    gitCommitChanges,
    gitPush,
    gitPull,
    generateAiCommit
  } = useStudio();

  const [commitMessage, setCommitMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  if (activeModal !== 'git') return null;

  const handleAiCommit = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setCommitMessage(generateAiCommit());
      setIsGenerating(false);
    }, 400);
  };

  const handleCommit = () => {
    if (!commitMessage.trim()) return;
    gitCommitChanges(commitMessage);
    setCommitMessage('');
  };

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-5xl shadow-2xl space-y-3.5 max-h-[92vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-purple-950 border border-purple-600/40 rounded-xl text-purple-400">
              <GitBranch className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-sm text-slate-100">Contrôle de Version Git & GitHub GUI</h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
                  {gitBranch}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  À jour
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Graphe visuel des commits, génération de messages par IA et synchronisation 1-clic
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={gitPull}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer"
            >
              <ArrowDown className="w-3.5 h-3.5 text-sky-400" />
              <span>Pull</span>
            </button>
            <button
              onClick={gitPush}
              className="px-2.5 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition shadow cursor-pointer"
            >
              <ArrowUp className="w-3.5 h-3.5" />
              <span>Push</span>
            </button>
            <button
              onClick={closeModal}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Main Grid (Changes & Commit Box + Commit Graph) */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-3 min-h-0 overflow-hidden">
          {/* Left: Changes & Commit Input */}
          <div className="md:col-span-5 flex flex-col space-y-2.5 min-h-0">
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex-1 flex flex-col min-h-0 overflow-hidden">
              <span className="text-xs font-bold text-slate-300 mb-2 flex items-center gap-1.5 flex-shrink-0">
                <FileDiff className="w-3.5 h-3.5 text-amber-400" />
                <span>Fichiers Modifiés ({gitFiles.length})</span>
              </span>
              <div className="flex-1 overflow-y-auto space-y-1 text-xs font-mono text-slate-300 pr-1">
                {gitFiles.map(file => (
                  <div
                    key={file.path}
                    className="p-2 bg-slate-900/60 rounded border border-slate-800 flex items-center justify-between text-[11px]"
                  >
                    <span className="truncate">{file.path}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded font-bold uppercase ${
                        file.status === 'modified'
                          ? 'bg-amber-950 text-amber-400 border border-amber-800'
                          : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      }`}
                    >
                      {file.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Commit Box */}
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300">Message de Commit</span>
                <button
                  onClick={handleAiCommit}
                  disabled={isGenerating}
                  className="px-2 py-0.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded text-[10px] font-bold flex items-center gap-1 shadow-sm cursor-pointer"
                >
                  <Sparkles className="w-3 h-3 text-amber-300" />
                  <span>{isGenerating ? 'Génération...' : 'Générer par IA'}</span>
                </button>
              </div>
              <textarea
                value={commitMessage}
                onChange={e => setCommitMessage(e.target.value)}
                rows={2}
                placeholder="feat: description conventionnelle..."
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white placeholder-slate-500 outline-none focus:border-purple-500 font-mono resize-none"
              />
              <button
                onClick={handleCommit}
                disabled={!commitMessage.trim()}
                className="w-full py-1.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-40 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 shadow cursor-pointer"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Valider le Commit (git commit)</span>
              </button>
            </div>
          </div>

          {/* Right: Visual Commit Graph */}
          <div className="md:col-span-7 bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col min-h-0 overflow-hidden">
            <span className="text-xs font-bold text-slate-300 mb-2 flex items-center gap-1.5 flex-shrink-0">
              <GitCommit className="w-3.5 h-3.5 text-purple-400" />
              <span>Graphe Visuel des Commits ({gitCommits.length})</span>
            </span>
            <div className="flex-1 overflow-y-auto space-y-2 font-mono text-xs pr-1">
              {gitCommits.map((c, i) => (
                <div
                  key={c.hash}
                  className="p-2.5 bg-[#060911] border border-slate-800/80 rounded-lg space-y-1 relative"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="flex items-center gap-1.5 text-purple-300 font-bold">
                      <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                      <span>* [{c.shortHash}]</span>
                      <span className="text-white font-sans font-medium">{c.message}</span>
                    </span>
                    <span className="text-[10px] text-slate-500">{c.date}</span>
                  </div>
                  <div className="text-[10px] text-slate-400 pl-3.5">
                    Auteur: <span className="text-sky-300">{c.author}</span> sur branche{' '}
                    <span className="text-purple-400 font-semibold">{c.branch}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
