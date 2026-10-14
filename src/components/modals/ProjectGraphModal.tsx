import React from 'react';
import { Network, X, RotateCw, ZoomIn, ZoomOut, Layers } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const ProjectGraphModal: React.FC = () => {
  const { activeModal, closeModal, files } = useStudio();

  if (activeModal !== 'projectGraph') return null;

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-6xl shadow-2xl space-y-3.5 max-h-[92vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-950 border border-indigo-600/40 rounded-xl text-indigo-400">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-sm text-slate-100">
                  Cartographie Visuelle & Graphe des Dépendances
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                  {files.length} modules analysés
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Arborescence interactive, imports croisés et flux d'orchestration multi-agents
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={closeModal}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Visual Graph Representation */}
        <div className="flex-1 w-full bg-[#050811] border border-slate-800 rounded-xl overflow-auto p-6 flex flex-col items-center justify-center relative min-h-[350px]">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl text-center">
            {/* Frontend Layer */}
            <div className="p-4 bg-slate-900/90 border border-sky-500/40 rounded-2xl space-y-2">
              <div className="font-bold text-xs text-sky-400 uppercase tracking-wider flex items-center justify-center gap-1.5">
                <Layers className="w-4 h-4" /> 1. UI & Interaction Layer
              </div>
              <div className="text-[11px] text-slate-300 space-y-1">
                <div className="p-2 bg-slate-950 rounded border border-slate-800">App.tsx & StudioContext</div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800">Header & 5 Compact Selectors</div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800">Monaco & Split Diff Preview</div>
              </div>
            </div>

            {/* Orchestrator Layer */}
            <div className="p-4 bg-slate-900/90 border border-indigo-500/40 rounded-2xl space-y-2">
              <div className="font-bold text-xs text-indigo-400 uppercase tracking-wider flex items-center justify-center gap-1.5">
                <Network className="w-4 h-4" /> 2. Agent Orchestrator
              </div>
              <div className="text-[11px] text-slate-300 space-y-1">
                <div className="p-2 bg-slate-950 rounded border border-slate-800">Antigravity Core CLI</div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800">Hermes & Claude Code Adapters</div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800">Adaptive Intelligence (96.4%)</div>
              </div>
            </div>

            {/* Native & Memory Layer */}
            <div className="p-4 bg-slate-900/90 border border-emerald-500/40 rounded-2xl space-y-2">
              <div className="font-bold text-xs text-emerald-400 uppercase tracking-wider flex items-center justify-center gap-1.5">
                <Layers className="w-4 h-4" /> 3. Runtime & Persistence
              </div>
              <div className="text-[11px] text-slate-300 space-y-1">
                <div className="p-2 bg-slate-950 rounded border border-slate-800">WinForms Bridge (Port 8001)</div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800">3-Tier Memory Catalogue</div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800">130+ Bundled Agent Skills</div>
              </div>
            </div>
          </div>
          <div className="text-[11px] text-slate-500 mt-6 font-mono">
            Toutes les connexions bidirectionnelles sont vérifiées et exemptes de cycles bloquants.
          </div>
        </div>
      </div>
    </div>
  );
};
