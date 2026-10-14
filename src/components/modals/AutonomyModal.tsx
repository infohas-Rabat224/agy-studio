import React, { useState } from 'react';
import { ListTodo, Bell, Plus, X, RotateCw, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';
import { AutonomyTask } from '../../types';

export const AutonomyModal: React.FC = () => {
  const {
    activeModal,
    closeModal,
    autonomyTasks,
    addAutonomyTask,
    moveAutonomyTask
  } = useStudio();

  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState<'HIGH' | 'NORMAL' | 'LOW'>('NORMAL');

  if (activeModal !== 'autonomy') return null;

  const handleAddTask = () => {
    if (!newTaskTitle.trim()) return;
    addAutonomyTask(newTaskTitle, newTaskPriority);
    setNewTaskTitle('');
  };

  const testWindowsToast = () => {
    alert('🔔 [Notification Windows 11 Toast]\n"Ghost Mode : Tâche autonome exécutée avec succès en arrière-plan !"');
  };

  const cols: { status: AutonomyTask['status']; title: string; color: string }[] = [
    { status: 'ready', title: 'Prêt (Ready)', color: 'text-sky-400' },
    { status: 'in_progress', title: 'En Cours', color: 'text-amber-400' },
    { status: 'blocked', title: 'Bloqué', color: 'text-rose-400' },
    { status: 'done', title: 'Terminé (Done)', color: 'text-emerald-400' }
  ];

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-5xl shadow-2xl space-y-3.5 max-h-[92vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-amber-950 border border-amber-600/40 rounded-xl text-amber-400">
              <ListTodo className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-sm text-slate-100">File d'Attente d'Autonomie & Ghost Mode</h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                  tasks/QUEUE.md
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Gestion de tâches en arrière-plan, surveillance persistante et notifications Toast Windows 11
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={testWindowsToast}
              className="px-2.5 py-1 bg-amber-950 hover:bg-amber-900 text-amber-300 border border-amber-800 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer"
            >
              <Bell className="w-3.5 h-3.5" />
              <span>Test Toast Win11</span>
            </button>
            <button
              onClick={closeModal}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Quick Add Task Bar */}
        <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 p-2.5 rounded-xl text-xs flex-shrink-0">
          <input
            type="text"
            value={newTaskTitle}
            onChange={e => setNewTaskTitle(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAddTask()}
            placeholder="Nouvelle tâche autonome à exécuter..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-amber-500"
          />
          <select
            value={newTaskPriority}
            onChange={e => setNewTaskPriority(e.target.value as any)}
            className="bg-slate-900 border border-slate-700 text-slate-300 rounded-lg px-2 py-1.5 text-xs outline-none cursor-pointer"
          >
            <option value="NORMAL">Priorité Normal</option>
            <option value="HIGH">Priorité Haute [HIGH]</option>
            <option value="LOW">Priorité Basse [LOW]</option>
          </select>
          <button
            onClick={handleAddTask}
            className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold rounded-lg flex items-center gap-1 shadow cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Ajouter</span>
          </button>
        </div>

        {/* Kanban 4 Columns */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-3 min-h-0 overflow-y-auto">
          {cols.map(col => {
            const tasksInCol = autonomyTasks.filter(t => t.status === col.status);
            return (
              <div
                key={col.status}
                className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col space-y-2"
              >
                <div
                  className={`flex items-center justify-between text-xs font-bold ${col.color} pb-1 border-b border-slate-800`}
                >
                  <span>{col.title}</span>
                  <span className="bg-slate-800 px-1.5 py-0.2 rounded text-[10px] text-slate-300">
                    {tasksInCol.length}
                  </span>
                </div>
                <div className="space-y-2 flex-1 overflow-y-auto text-xs pr-1">
                  {tasksInCol.map(task => (
                    <div
                      key={task.id}
                      className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg space-y-1.5 hover:border-slate-700 transition"
                    >
                      <div className="flex items-start justify-between gap-1">
                        <span className="font-semibold text-white leading-tight">{task.title}</span>
                        <span
                          className={`text-[9px] px-1 py-0.2 rounded font-bold uppercase ${
                            task.priority === 'HIGH'
                              ? 'bg-rose-950 text-rose-400'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {task.priority}
                        </span>
                      </div>
                      {task.progressPercent !== undefined && task.status === 'in_progress' && (
                        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-amber-400 h-full rounded-full transition-all"
                            style={{ width: `${task.progressPercent}%` }}
                          />
                        </div>
                      )}
                      <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/60">
                        <span>Agent: {task.assignedAgent || 'auto'}</span>
                        <div className="flex gap-1">
                          {col.status !== 'ready' && (
                            <button
                              onClick={() => moveAutonomyTask(task.id, 'ready')}
                              className="hover:text-sky-400 cursor-pointer"
                              title="Déplacer vers Prêt"
                            >
                              ←
                            </button>
                          )}
                          {col.status !== 'done' && (
                            <button
                              onClick={() =>
                                moveAutonomyTask(
                                  task.id,
                                  col.status === 'ready' ? 'in_progress' : 'done'
                                )
                              }
                              className="hover:text-emerald-400 cursor-pointer"
                              title="Avancer le statut"
                            >
                              →
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
