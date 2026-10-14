import React, { useState } from 'react';
import { Swords, X, Play, Trophy, Zap } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const AgentDuelModal: React.FC = () => {
  const { activeModal, closeModal, agents } = useStudio();
  const [promptInput, setPromptInput] = useState('Écris un algorithme de recherche dichotomique en TypeScript avec gestion d\'erreurs');
  const [isDueling, setIsDueling] = useState(false);
  const [duelResults, setDuelResults] = useState<boolean>(true);

  if (activeModal !== 'agentDuel') return null;

  const handleStartDuel = () => {
    setIsDueling(true);
    setTimeout(() => {
      setIsDueling(false);
      setDuelResults(true);
    }, 1000);
  };

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl shadow-2xl space-y-4 max-h-[92vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-sky-950 border border-sky-600/40 rounded-xl text-sky-400">
              <Swords className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                Arène & Duel Comparatif Multi-Agents
              </h2>
              <p className="text-[11px] text-slate-400">
                Évaluez simultanément deux agents sur le même prompt pour comparer latence, qualité et consommation
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

        {/* Prompt Input */}
        <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 flex-shrink-0 text-xs">
          <label className="font-bold text-slate-300">Prompt du Duel :</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={promptInput}
              onChange={e => setPromptInput(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white outline-none focus:border-sky-500 font-mono"
            />
            <button
              onClick={handleStartDuel}
              disabled={isDueling}
              className="px-4 py-1.5 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-bold rounded-lg flex items-center gap-1.5 shadow cursor-pointer"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{isDueling ? 'Comparaison en cours...' : 'Lancer le Duel'}</span>
            </button>
          </div>
        </div>

        {/* Duel Side-by-Side comparison */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3 min-h-0 overflow-y-auto">
          {/* Agent 1: Antigravity */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col space-y-2">
            <div className="flex items-center justify-between pb-1 border-b border-slate-800 text-xs">
              <span className="font-bold text-sky-400 flex items-center gap-1.5">
                <Trophy className="w-4 h-4 text-amber-400" />
                <span>Antigravity (Gemini 3.8 Flash)</span>
              </span>
              <span className="text-[10px] font-mono text-emerald-400">142ms • 210 tokens</span>
            </div>
            <pre className="flex-1 p-2 bg-[#050811] rounded text-[11px] font-mono text-slate-300 overflow-y-auto whitespace-pre-wrap select-text">
{`function binarySearch<T>(arr: T[], target: T): number {
  let left = 0;
  let right = arr.length - 1;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (arr[mid] === target) return mid;
    if (arr[mid] < target) left = mid + 1;
    else right = mid - 1;
  }
  return -1;
}`}
            </pre>
          </div>

          {/* Agent 2: Claude Code CLI */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col space-y-2">
            <div className="flex items-center justify-between pb-1 border-b border-slate-800 text-xs">
              <span className="font-bold text-amber-400 flex items-center gap-1.5">
                <span>Claude Code (Claude 3.7 Sonnet)</span>
              </span>
              <span className="text-[10px] font-mono text-slate-400">380ms • 240 tokens</span>
            </div>
            <pre className="flex-1 p-2 bg-[#050811] rounded text-[11px] font-mono text-slate-300 overflow-y-auto whitespace-pre-wrap select-text">
{`export function binarySearch<T>(
  sortedList: readonly T[],
  item: T,
  comparator: (a: T, b: T) => number = (a, b) => (a < b ? -1 : a > b ? 1 : 0)
): number {
  let low = 0;
  let high = sortedList.length - 1;
  while (low <= high) {
    const mid = (low + high) >>> 1;
    const cmp = comparator(sortedList[mid], item);
    if (cmp === 0) return mid;
    if (cmp < 0) low = mid + 1;
    else high = mid - 1;
  }
  return -1;
}`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
