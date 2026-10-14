import React from 'react';
import { Kanban, X, Bot, Clock, Plus } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const KanbanModal: React.FC = () => {
  const { activeModal, closeModal, autonomyTasks, agents } = useStudio();

  if (activeModal !== 'kanban') return null;

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-5xl shadow-2xl space-y-3.5 max-h-[92vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-cyan-950 border border-cyan-600/40 rounded-xl text-cyan-400">
              <Kanban className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-sm text-slate-100">
                  Tableau Kanban Visuel & Orchestration Multi-Agents
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                  Multi-Agent Live
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Suivi de la charge de travail et répartition des objectifs par agent
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

        {/* Agents Load Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 flex-shrink-0 text-xs">
          {agents.slice(0, 4).map(a => (
            <div key={a.id} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200">{a.name.split(' ')[0]}</span>
                <span className="text-[10px] font-mono text-emerald-400">Actif</span>
              </div>
              <div className="text-[10px] text-slate-500 truncate">{a.defaultModel}</div>
            </div>
          ))}
        </div>

        {/* Kanban Board Columns */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3 min-h-0 overflow-y-auto">
          {/* Backlog */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-sky-400 pb-1 border-b border-slate-800">
              <span>Backlog Global</span>
              <span className="bg-slate-800 px-1.5 py-0.2 rounded text-[10px] text-slate-300">
                {autonomyTasks.filter(t => t.status === 'ready').length}
              </span>
            </div>
            <div className="space-y-2 flex-1 overflow-y-auto text-xs pr-1">
              {autonomyTasks
                .filter(t => t.status === 'ready')
                .map(t => (
                  <div key={t.id} className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg space-y-1">
                    <div className="font-semibold text-white">{t.title}</div>
                    <div className="text-[10px] text-slate-400">Agent: {t.assignedAgent}</div>
                  </div>
                ))}
            </div>
          </div>

          {/* In Execution */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-amber-400 pb-1 border-b border-slate-800">
              <span>En Exécution</span>
              <span className="bg-slate-800 px-1.5 py-0.2 rounded text-[10px] text-slate-300">
                {autonomyTasks.filter(t => t.status === 'in_progress').length}
              </span>
            </div>
            <div className="space-y-2 flex-1 overflow-y-auto text-xs pr-1">
              {autonomyTasks
                .filter(t => t.status === 'in_progress')
                .map(t => (
                  <div key={t.id} className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg space-y-1.5">
                    <div className="font-semibold text-white">{t.title}</div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-amber-400 h-full rounded-full"
                        style={{ width: `${t.progressPercent || 50}%` }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Validated */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-emerald-400 pb-1 border-b border-slate-800">
              <span>Validé & Archivé</span>
              <span className="bg-slate-800 px-1.5 py-0.2 rounded text-[10px] text-slate-300">
                {autonomyTasks.filter(t => t.status === 'done').length}
              </span>
            </div>
            <div className="space-y-2 flex-1 overflow-y-auto text-xs pr-1">
              {autonomyTasks
                .filter(t => t.status === 'done')
                .map(t => (
                  <div key={t.id} className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg space-y-1">
                    <div className="font-semibold text-emerald-300">{t.title}</div>
                    <div className="text-[10px] text-slate-500">100% exécuté</div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
