import React, { useState, useEffect } from 'react';
import {
  Search,
  Code2,
  Terminal,
  GitBranch,
  ListTodo,
  Network,
  Key,
  Cloud,
  Eye,
  Bot,
  Gauge,
  Database,
  FileText,
  X
} from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const CommandPalette: React.FC = () => {
  const { activeModal, closeModal, openModal, sendMessage, setThinkingMode } = useStudio();
  const [query, setQuery] = useState('');

  if (activeModal !== 'commandPalette') return null;

  const commands = [
    { id: 'monaco', label: 'Ouvrir l\'Éditeur Monaco & Split Diff', icon: <Code2 className="w-4 h-4 text-sky-400" />, action: () => openModal('monaco') },
    { id: 'git', label: 'Ouvrir Git GUI & Graphe des Commits', icon: <GitBranch className="w-4 h-4 text-purple-400" />, action: () => openModal('git') },
    { id: 'terminal', label: 'Basculer le Terminal Interactif (PowerShell)', icon: <Terminal className="w-4 h-4 text-emerald-400" />, action: () => openModal('terminal') },
    { id: 'autonomy', label: 'Ouvrir la File d\'Attente d\'Autonomie (Ghost Mode)', icon: <ListTodo className="w-4 h-4 text-amber-400" />, action: () => openModal('autonomy') },
    { id: 'graph', label: 'Afficher la Cartographie des Dépendances (Mermaid)', icon: <Network className="w-4 h-4 text-indigo-400" />, action: () => openModal('projectGraph') },
    { id: 'vault', label: 'Gérer le Coffre de Secrets (.env Vault)', icon: <Key className="w-4 h-4 text-rose-400" />, action: () => openModal('vault') },
    { id: 'deploy', label: 'Lancer un Déploiement Cloud (Cloudflare / Vercel)', icon: <Cloud className="w-4 h-4 text-teal-400" />, action: () => openModal('deploy') },
    { id: 'reflex', label: 'Lancer l\'Audit Visuel Vision Reflex', icon: <Eye className="w-4 h-4 text-pink-400" />, action: () => openModal('visionReflex') },
    { id: 'model', label: 'Changer le Modèle d\'IA (Gemini / Claude)', icon: <Bot className="w-4 h-4 text-sky-400" />, action: () => openModal('model') },
    { id: 'quota', label: 'Consulter les Quotas Réels (/quota)', icon: <Gauge className="w-4 h-4 text-emerald-400" />, action: () => openModal('quota') },
    { id: 'memory', label: 'Ouvrir le Catalogue Mémoire (3-Tier)', icon: <Database className="w-4 h-4 text-rose-400" />, action: () => openModal('memory') },
    { id: 'report', label: 'Générer le Rapport Consolidé de Session', icon: <FileText className="w-4 h-4 text-indigo-400" />, action: () => openModal('sessionReport') },
    { id: 'plan', label: 'Générer un Plan d\'Exécution (/plan)', icon: <Code2 className="w-4 h-4 text-sky-400" />, action: () => sendMessage('/plan ') },
    { id: 'boost', label: 'Activer le Raisonnement Approfondi (/boost)', icon: <Bot className="w-4 h-4 text-indigo-400" />, action: () => sendMessage('/boost ') }
  ];

  const filtered = commands.filter(c =>
    c.label.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-start justify-center pt-20 p-4 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Search header */}
        <div className="p-3 bg-slate-950 flex items-center gap-2 border-b border-slate-800">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Rechercher une commande, un outil ou un raccourci..."
            className="flex-1 bg-transparent border-none text-white text-xs placeholder-slate-500 outline-none"
            autoFocus
          />
          <button
            onClick={closeModal}
            className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results list */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1 text-xs">
          {filtered.map(cmd => (
            <button
              key={cmd.id}
              onClick={() => {
                closeModal();
                cmd.action();
              }}
              className="w-full p-2 rounded-lg text-left text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-3 transition cursor-pointer"
            >
              {cmd.icon}
              <span className="font-medium">{cmd.label}</span>
            </button>
          ))}
          {filtered.length === 0 && (
            <div className="p-4 text-center text-slate-500 text-xs">
              Aucune commande trouvée.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
