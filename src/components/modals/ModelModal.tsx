import React from 'react';
import { Bot, X, Check, Cpu, Zap, Sparkles } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const ModelModal: React.FC = () => {
  const { activeModal, closeModal, models, currentModel, setCurrentModel } = useStudio();

  if (activeModal !== 'model') return null;

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-sky-950/80 border border-sky-600/40 rounded-xl text-sky-400">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-100">
                Changer le Modèle d'Intelligence Artificielle
              </h2>
              <p className="text-[11px] text-slate-400">
                Actif pour toutes les instructions dans Agy Studio et le moteur agy CLI
              </p>
            </div>
          </div>
          <button
            onClick={closeModal}
            className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Active Model Banner */}
        <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl flex items-center justify-between flex-shrink-0">
          <div className="text-xs text-slate-300 font-medium">Modèle actuellement configuré :</div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="font-mono font-bold text-xs px-2.5 py-1 bg-sky-950 text-sky-300 border border-sky-600/50 rounded-lg">
              {currentModel}
            </span>
          </div>
        </div>

        {/* Model Cards List */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
          {models.map(m => {
            const isSelected = currentModel === m.name;
            return (
              <div
                key={m.id}
                onClick={() => {
                  setCurrentModel(m.name);
                  closeModal();
                }}
                className={`p-4 rounded-xl border transition cursor-pointer flex flex-col space-y-2 ${
                  isSelected
                    ? 'bg-sky-950/50 border-sky-500 shadow-md'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 font-bold text-sm text-white">
                    <Cpu className="w-4 h-4 text-sky-400" />
                    <span>{m.name}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {m.badge}
                    </span>
                  </div>
                  {isSelected && (
                    <span className="text-emerald-400 flex items-center gap-1 font-bold text-xs">
                      <Check className="w-4 h-4" /> Actif
                    </span>
                  )}
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">{m.description}</p>
                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-900">
                  <span>Fournisseur: {m.provider}</span>
                  <span>Contexte: {m.contextWindow} • Latence: {m.latency}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-3 flex items-center justify-between text-[11px] flex-shrink-0">
          <span className="text-slate-500 font-mono">
            Astuce : tapez <code>/model &lt;id&gt;</code> dans le prompt
          </span>
          <button
            onClick={closeModal}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-semibold cursor-pointer"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};
