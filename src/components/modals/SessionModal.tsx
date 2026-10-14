import React, { useState } from 'react';
import { Layers, X, Plus, Search, Pin, Star, GitBranch, Trash2, Edit } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const SessionModal: React.FC = () => {
  const {
    activeModal,
    closeModal,
    sessions,
    activeSessionId,
    switchSession,
    createSession,
    togglePinSession,
    toggleFavoriteSession,
    renameSession,
    forkSession,
    deleteSession
  } = useStudio();

  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'pinned' | 'favorites'>('all');

  if (activeModal !== 'session') return null;

  const filteredSessions = sessions.filter(s => {
    const matchFilter =
      filter === 'all' ||
      (filter === 'pinned' && s.pinned) ||
      (filter === 'favorites' && s.favorite);
    const matchSearch = s.title.toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl shadow-2xl space-y-4 max-h-[92vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-950 border border-indigo-600/40 rounded-xl text-indigo-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-sm text-slate-100">
                  Gestionnaire de Sessions & Continuité
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                  {sessions.length} sessions
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Sessions persistantes, reprise non-destructive, épinglage et lignée
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                createSession();
                closeModal();
              }}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1 shadow cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Nouvelle Session</span>
            </button>
            <button
              onClick={closeModal}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 bg-slate-950 p-2 rounded-xl border border-slate-800 text-xs">
          <div className="flex items-center gap-2 flex-1 min-w-[200px]">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Rechercher par nom..."
              className="bg-transparent border-none text-xs text-white placeholder-slate-500 focus:outline-none w-full"
            />
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => setFilter('all')}
              className={`px-2.5 py-1 rounded text-[11px] font-semibold cursor-pointer ${
                filter === 'all' ? 'bg-indigo-600 text-white' : 'bg-slate-900 text-slate-400 hover:text-white'
              }`}
            >
              Toutes ({sessions.length})
            </button>
            <button
              onClick={() => setFilter('pinned')}
              className={`px-2.5 py-1 rounded text-[11px] font-semibold cursor-pointer flex items-center gap-1 ${
                filter === 'pinned' ? 'bg-amber-600 text-white' : 'bg-slate-900 text-amber-300 hover:bg-slate-800'
              }`}
            >
              <Pin className="w-3 h-3" /> Épinglées
            </button>
            <button
              onClick={() => setFilter('favorites')}
              className={`px-2.5 py-1 rounded text-[11px] font-semibold cursor-pointer flex items-center gap-1 ${
                filter === 'favorites' ? 'bg-amber-600 text-white' : 'bg-slate-900 text-amber-300 hover:bg-slate-800'
              }`}
            >
              <Star className="w-3 h-3" /> Favoris
            </button>
          </div>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1 text-xs">
          {filteredSessions.map(sess => {
            const isActive = sess.id === activeSessionId;
            return (
              <div
                key={sess.id}
                className={`p-3 rounded-xl border transition flex items-center justify-between ${
                  isActive
                    ? 'bg-indigo-950/40 border-indigo-500'
                    : 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div
                  onClick={() => {
                    switchSession(sess.id);
                    closeModal();
                  }}
                  className="space-y-1 flex-1 cursor-pointer pr-3"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-xs">{sess.title}</span>
                    {isActive && (
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-indigo-900 text-indigo-300 font-mono">
                        Active
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-slate-400 font-mono">
                    <span>Agent: {sess.agent}</span>
                    <span>• Mode: {sess.mode}</span>
                    <span>• Modifié : {sess.updatedAt}</span>
                    <span>• {sess.messageCount} messages</span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <button
                    onClick={() => togglePinSession(sess.id)}
                    className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 cursor-pointer"
                    title={sess.pinned ? 'Désépingler' : 'Épingler'}
                  >
                    <Pin className={`w-3.5 h-3.5 ${sess.pinned ? 'text-amber-400' : 'text-slate-500'}`} />
                  </button>
                  <button
                    onClick={() => toggleFavoriteSession(sess.id)}
                    className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 cursor-pointer"
                    title={sess.favorite ? 'Retirer des favoris' : 'Favori'}
                  >
                    <Star
                      className={`w-3.5 h-3.5 ${sess.favorite ? 'text-amber-400 fill-amber-400' : 'text-slate-500'}`}
                    />
                  </button>
                  <button
                    onClick={() => forkSession(sess.id)}
                    className="p-1 text-slate-400 hover:text-purple-400 rounded hover:bg-slate-800 cursor-pointer"
                    title="Forker"
                  >
                    <GitBranch className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      const t = prompt('Renommer session :', sess.title);
                      if (t) renameSession(sess.id, t);
                    }}
                    className="p-1 text-slate-400 hover:text-sky-400 rounded hover:bg-slate-800 cursor-pointer"
                    title="Renommer"
                  >
                    <Edit className="w-3.5 h-3.5" />
                  </button>
                  {sessions.length > 1 && (
                    <button
                      onClick={() => deleteSession(sess.id)}
                      className="p-1 text-slate-400 hover:text-rose-400 rounded hover:bg-slate-800 cursor-pointer"
                      title="Supprimer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
