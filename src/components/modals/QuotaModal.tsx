import React, { useState } from 'react';
import { Gauge, X, RefreshCw } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const QuotaModal: React.FC = () => {
  const { activeModal, closeModal, quotas } = useStudio();
  const [isRefreshing, setIsRefreshing] = useState(false);

  if (activeModal !== 'quota') return null;

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-5 shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Gauge className="w-5 h-5 text-emerald-400" />
            <h2 className="font-bold text-sm text-slate-100">
              Quotas & Limites en Temps Réel (Antigravity)
            </h2>
          </div>
          <button
            onClick={closeModal}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Quota gauges */}
        <div className="space-y-3">
          {quotas.map(q => (
            <div key={q.name} className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-200">{q.name}</span>
                <span className="font-mono text-emerald-400">{q.used.toLocaleString()} / {q.limit.toLocaleString()} {q.unit}</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(q.percent, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>{q.percent}% consommé</span>
                <span>Reset dans : {q.resetIn}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-3 flex items-center justify-between text-[11px]">
          <span className="text-slate-500 font-mono">Source : agy CLI -p /quota</span>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold flex items-center gap-1.5 cursor-pointer shadow"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Rafraîchir les Quotas</span>
          </button>
        </div>
      </div>
    </div>
  );
};
