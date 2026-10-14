import React, { useState } from 'react';
import { Database, X, Plus, Search, Tag, Check, Award } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';
import { MemoryItem } from '../../types';

export const MemoryModal: React.FC = () => {
  const { activeModal, closeModal, memoryItems, addMemoryItem } = useStudio();
  const [selectedTier, setSelectedTier] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newTier, setNewTier] = useState<MemoryItem['tier']>('procedural');

  if (activeModal !== 'memory') return null;

  const handleAdd = () => {
    if (!newTitle.trim() || !newContent.trim()) return;
    addMemoryItem(newTier, newTitle.trim(), newContent.trim(), ['Manuel']);
    setNewTitle('');
    setNewContent('');
  };

  const filteredItems = memoryItems.filter(item => {
    const matchTier = selectedTier === 'all' || item.tier === selectedTier;
    const matchQuery =
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.content.toLowerCase().includes(searchQuery.toLowerCase());
    return matchTier && matchQuery;
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
            <div className="p-2 bg-rose-950 border border-rose-600/40 rounded-xl text-rose-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-sm text-slate-100">
                  Catalogue Mémoire Adaptative (3-Tier)
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
                  {memoryItems.length} entrées
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Épisodique (sessions passées), Sémantique (concepts & docs), Procédurale (workflows validés)
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

        {/* Filter bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 bg-slate-950 p-2 rounded-xl border border-slate-800 text-xs">
          <div className="flex items-center gap-2 flex-1 min-w-[200px]">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Rechercher dans la mémoire..."
              className="bg-transparent border-none text-xs text-white placeholder-slate-500 focus:outline-none w-full"
            />
          </div>
          <div className="flex gap-1">
            {(['all', 'procedural', 'semantic', 'episodic'] as const).map(tier => (
              <button
                key={tier}
                onClick={() => setSelectedTier(tier)}
                className={`px-2.5 py-1 rounded text-[11px] font-semibold cursor-pointer capitalize ${
                  selectedTier === tier
                    ? 'bg-rose-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:text-white'
                }`}
              >
                {tier === 'all' ? 'Toutes' : tier}
              </button>
            ))}
          </div>
        </div>

        {/* Items List */}
        <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 text-xs">
          {filteredItems.map(item => (
            <div
              key={item.id}
              className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-xs flex items-center gap-2">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      item.tier === 'procedural'
                        ? 'bg-purple-400'
                        : item.tier === 'semantic'
                        ? 'bg-sky-400'
                        : 'bg-amber-400'
                    }`}
                  />
                  <span>{item.title}</span>
                </span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {item.tier} • Confiance {(item.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">{item.content}</p>
              <div className="flex items-center gap-1.5 pt-1 text-[10px] text-slate-500">
                <Tag className="w-3 h-3 text-slate-500" />
                <span>{item.tags.join(', ')}</span>
                <span>• Accédé {item.accessCount} fois</span>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-3 flex justify-end">
          <button
            onClick={closeModal}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold cursor-pointer"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};
