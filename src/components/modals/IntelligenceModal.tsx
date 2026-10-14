import React, { useState } from 'react';
import { Sparkles, X, TrendingUp, Compass, ShieldAlert, Award, Database, Check } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const IntelligenceModal: React.FC = () => {
  const { activeModal, closeModal, openModal } = useStudio();
  const [activeTab, setActiveTab] = useState<'overview' | 'strategies' | 'performance' | 'risks'>('overview');

  if (activeModal !== 'intelligence') return null;

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
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-sm text-slate-100">
                  Dashboard Intelligence Adaptative v2.6
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                  ✦ Active Learning
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Distillation dynamique des patterns, capitalisation des succès et calibration du score de confiance
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

        {/* Tabs */}
        <div className="flex gap-2 border-b border-slate-800 pb-2 text-xs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1.5 rounded-lg font-semibold cursor-pointer transition ${
              activeTab === 'overview' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Vue d'Ensemble
          </button>
          <button
            onClick={() => setActiveTab('strategies')}
            className={`px-3 py-1.5 rounded-lg font-semibold cursor-pointer transition ${
              activeTab === 'strategies' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Stratégies Apprises (42)
          </button>
          <button
            onClick={() => setActiveTab('performance')}
            className={`px-3 py-1.5 rounded-lg font-semibold cursor-pointer transition ${
              activeTab === 'performance' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Performance Agents (96.4%)
          </button>
          <button
            onClick={() => setActiveTab('risks')}
            className={`px-3 py-1.5 rounded-lg font-semibold cursor-pointer transition ${
              activeTab === 'risks' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Risques & Régressions (0)
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
          {activeTab === 'overview' && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                  <div className="text-[10px] text-slate-400">Confiance Globale</div>
                  <div className="text-xl font-bold text-emerald-400 font-mono">96.4%</div>
                </div>
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                  <div className="text-[10px] text-slate-400">Patterns Capturés</div>
                  <div className="text-xl font-bold text-sky-400 font-mono">128</div>
                </div>
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                  <div className="text-[10px] text-slate-400">Régressions Évitées</div>
                  <div className="text-xl font-bold text-amber-400 font-mono">19</div>
                </div>
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                  <div className="text-[10px] text-slate-400">Mémoire Procédurale</div>
                  <div className="text-xl font-bold text-purple-400 font-mono">34 flux</div>
                </div>
              </div>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                <div className="font-bold text-slate-200">Synthèse d'Apprentissage Continu</div>
                <p className="text-slate-400 leading-relaxed text-[11px]">
                  Le système Agy Studio v2.6 analyse les résultats de compilation, d'exécution de code et les feedbacks de relectures. Chaque succès est synthétisé sous forme d'heuristiques mémorisées dans le catalogue à 3 niveaux.
                </p>
                <div className="pt-2">
                  <button
                    onClick={() => {
                      closeModal();
                      openModal('memory');
                    }}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg flex items-center gap-1.5 shadow cursor-pointer text-xs"
                  >
                    <Database className="w-3.5 h-3.5" />
                    <span>Explorer le Catalogue Mémoire (3-Tier)</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'strategies' && (
            <div className="space-y-2">
              {[
                { title: 'Validation Stricte ATAM 42 Pages', desc: 'Ne jamais tronquer les cellules de tableaux Word lors de la génération PDF.' },
                { title: 'Isolation du Sélecteur Win32 Bridge', desc: 'Toujours sonder 127.0.0.1:8001 avant le fallback manuel pour fluidité Windows 11.' },
                { title: 'Atomic Snapshot avant Refactoring', desc: 'Enregistrer l\'état Git local immédiatement avant toute modification multi-fichiers.' }
              ].map((s, idx) => (
                <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                  <div className="font-bold text-sky-400 flex items-center gap-2">
                    <Compass className="w-4 h-4" />
                    <span>{s.title}</span>
                  </div>
                  <div className="text-slate-400 text-[11px]">{s.desc}</div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'performance' && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
              <div className="font-bold text-slate-200">Précision par Agent</div>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span>Antigravity (Local)</span>
                    <span className="font-mono text-emerald-400">98.2%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-full rounded-full" style={{ width: '98.2%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span>Claude Code CLI</span>
                    <span className="font-mono text-indigo-400">97.0%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-indigo-500 h-full rounded-full" style={{ width: '97%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span>Hermes Orchestrator</span>
                    <span className="font-mono text-sky-400">95.5%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-sky-500 h-full rounded-full" style={{ width: '95.5%' }} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'risks' && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
              <div className="font-bold text-emerald-400 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4" />
                <span>Aucune régression détectée sur le projet</span>
              </div>
              <p className="text-slate-400 text-[11px]">
                Le gardien d'intégrité surveille en continu la conformité des types TypeScript, les imports et les dépendances.
              </p>
            </div>
          )}
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
