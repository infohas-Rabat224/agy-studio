import React, { useState } from 'react';
import { Network, X, Plus, Globe, Terminal, GitBranch, Settings2, CheckCircle2 } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const McpModal: React.FC = () => {
  const { activeModal, closeModal, mcpServers, addMcpServer } = useStudio();
  const [showAddForm, setShowAddForm] = useState(false);
  const [serverName, setServerName] = useState('');
  const [category, setCategory] = useState<'wordpress' | 'vps' | 'github' | 'custom'>('wordpress');
  const [endpoint, setEndpoint] = useState('');

  if (activeModal !== 'mcp') return null;

  const handleAdd = () => {
    if (!serverName.trim() || !endpoint.trim()) return;
    addMcpServer(serverName.trim(), category, endpoint.trim());
    setServerName('');
    setEndpoint('');
    setShowAddForm(false);
  };

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case 'wordpress':
        return <Globe className="w-4 h-4 text-sky-400" />;
      case 'vps':
        return <Terminal className="w-4 h-4 text-emerald-400" />;
      case 'github':
        return <GitBranch className="w-4 h-4 text-purple-400" />;
      default:
        return <Settings2 className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4 bg-slate-950/70 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-950/80 border border-indigo-700/50 rounded-xl text-indigo-400">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                Serveurs & Outils MCP (Model Context Protocol)
                <span className="text-[10px] bg-indigo-900/60 text-indigo-300 border border-indigo-700/60 px-2 py-0.5 rounded-full font-mono">
                  {mcpServers.length}
                </span>
              </h2>
              <p className="text-[11px] text-slate-400">
                Connectez vos serveurs WordPress (vibecoding & blog), VPS/SSH (exécution à distance) et GitHub
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow transition cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" /> Nouveau Serveur
            </button>
            <button
              onClick={closeModal}
              className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Add Form (Collapsible) */}
        {showAddForm && (
          <div className="border-b border-indigo-900/40 bg-slate-950/95 p-4 space-y-3 flex-shrink-0 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <input
                type="text"
                value={serverName}
                onChange={e => setServerName(e.target.value)}
                placeholder="Nom unique (ex: mon-wordpress)"
                className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-100 font-mono text-xs outline-none focus:border-indigo-500"
              />
              <select
                value={category}
                onChange={e => setCategory(e.target.value as any)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-100 text-xs outline-none cursor-pointer"
              >
                <option value="wordpress">WordPress (Blog & Vibecoding)</option>
                <option value="vps">VPS / SSH Instance</option>
                <option value="github">GitHub MCP Server</option>
                <option value="custom">Personnalisé / Stdio</option>
              </select>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={endpoint}
                  onChange={e => setEndpoint(e.target.value)}
                  placeholder="URL ou commande"
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-100 font-mono text-xs outline-none focus:border-indigo-500"
                />
                <button
                  onClick={handleAdd}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg cursor-pointer"
                >
                  Ajouter
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Servers List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {mcpServers.map(s => (
            <div
              key={s.id}
              className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-white">
                  {getCategoryIcon(s.category)}
                  <span>{s.name}</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1 font-semibold">
                  <CheckCircle2 className="w-3 h-3" /> Connecté
                </span>
              </div>
              <div className="text-[11px] font-mono text-slate-400 truncate">
                Endpoint: <span className="text-sky-300">{s.endpoint}</span>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-1 border-t border-slate-900">
                {s.tools.map(tool => (
                  <span
                    key={tool}
                    className="text-[10px] bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-indigo-300 font-mono"
                  >
                    tool:{tool}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
