import React from 'react';
import { History, X, RotateCcw, FileText, CheckCircle2 } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const TimeMachineModal: React.FC = () => {
  const { activeModal, closeModal, timeMachineSnapshots, rollbackSnapshot } = useStudio();

  if (activeModal !== 'timeMachine') return null;

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl shadow-2xl space-y-4 max-h-[90vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-amber-950 border border-amber-600/40 rounded-xl text-amber-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                Time-Machine Rollback (Undo 1-Clic par Tour)
              </h2>
              <p className="text-[11px] text-slate-400">
                Instantanés atomiques créés avant chaque modification de code pour une réversibilité totale
              </p>
            </div>
          </div>
          <button
            onClick={closeModal}
            className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Snapshots list */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
          {timeMachineSnapshots.map(snap => (
            <div
              key={snap.id}
              className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2 hover:border-amber-500/50 transition"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200 text-xs flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                  <span>{snap.prompt}</span>
                </span>
                <span className="text-[10px] font-mono text-slate-500">{snap.timestamp}</span>
              </div>
              <div className="flex flex-wrap gap-2 text-[10px] text-slate-400 font-mono">
                <span>Agent: <strong className="text-sky-300">{snap.agent}</strong></span>
                <span>•</span>
                <span>Diff: <strong className="text-emerald-400">{snap.diffSummary}</strong></span>
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
                <span className="text-[10px] text-slate-500 truncate max-w-sm">
                  Fichiers : {snap.filesChanged.join(', ')}
                </span>
                <button
                  onClick={() => rollbackSnapshot(snap.id)}
                  className="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1 shadow cursor-pointer"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Restaurer cet état</span>
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-3 flex items-center justify-between text-[11px] text-slate-400">
          <span className="text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> 100% sans risque de perte de données
          </span>
          <button
            onClick={closeModal}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-semibold cursor-pointer"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};
