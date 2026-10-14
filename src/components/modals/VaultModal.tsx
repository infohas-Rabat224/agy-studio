import React, { useState } from 'react';
import { Key, X, Eye, EyeOff, Plus, Trash2, Copy, Check, ShieldCheck } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';
import { VaultSecret } from '../../types';

export const VaultModal: React.FC = () => {
  const {
    activeModal,
    closeModal,
    vaultSecrets,
    saveVaultSecret,
    deleteVaultSecret,
    toggleVaultSecretMask
  } = useStudio();

  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [newProvider, setNewProvider] = useState<VaultSecret['provider']>('Gemini');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (activeModal !== 'vault') return null;

  const handleAdd = () => {
    if (!newKey.trim() || !newValue.trim()) return;
    saveVaultSecret(newKey.trim(), newValue.trim(), newProvider);
    setNewKey('');
    setNewValue('');
  };

  const handleCopy = (val: string, id: string) => {
    navigator.clipboard.writeText(val);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl space-y-4 max-h-[90vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-rose-950 border border-rose-600/40 rounded-xl text-rose-400">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                Coffre-fort de Clés & Variables d'Environnement (.env Vault)
              </h2>
              <p className="text-[11px] text-slate-400">
                Masquage automatique des secrets et protection stricte contre les fuites
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

        {/* Add Key form */}
        <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 flex-shrink-0 text-xs">
          <div className="font-semibold text-slate-300">Ajouter un nouveau secret</div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input
              type="text"
              value={newKey}
              onChange={e => setNewKey(e.target.value)}
              placeholder="Nom (ex: GEMINI_API_KEY)"
              className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-500 font-mono outline-none"
            />
            <input
              type="password"
              value={newValue}
              onChange={e => setNewValue(e.target.value)}
              placeholder="Valeur du secret"
              className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-500 font-mono outline-none"
            />
            <div className="flex gap-2">
              <select
                value={newProvider}
                onChange={e => setNewProvider(e.target.value as any)}
                className="flex-1 bg-slate-900 border border-slate-700 text-slate-300 rounded-lg px-2 py-1.5 text-xs outline-none cursor-pointer"
              >
                <option value="Gemini">Gemini</option>
                <option value="Anthropic">Anthropic</option>
                <option value="OpenAI">OpenAI</option>
                <option value="Cloudflare">Cloudflare</option>
                <option value="GitHub">GitHub</option>
                <option value="Custom">Autre</option>
              </select>
              <button
                onClick={handleAdd}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-lg flex items-center gap-1 shadow cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Secrets list */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {vaultSecrets.map(sec => (
            <div
              key={sec.id}
              className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl flex items-center justify-between text-xs font-mono"
            >
              <div className="space-y-0.5 min-w-0 pr-2">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white text-[11px] truncate">{sec.key}</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                    {sec.provider}
                  </span>
                </div>
                <div className="text-slate-400 text-[10px] truncate">
                  {sec.masked ? '••••••••••••••••••••••••••••••' : sec.value}
                </div>
              </div>

              <div className="flex items-center gap-1.5 flex-shrink-0">
                <button
                  onClick={() => toggleVaultSecretMask(sec.id)}
                  className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 cursor-pointer"
                  title={sec.masked ? 'Afficher' : 'Masquer'}
                >
                  {sec.masked ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={() => handleCopy(sec.value, sec.id)}
                  className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 cursor-pointer"
                  title="Copier"
                >
                  {copiedId === sec.id ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
                <button
                  onClick={() => deleteVaultSecret(sec.id)}
                  className="p-1 text-slate-400 hover:text-rose-400 rounded hover:bg-slate-800 cursor-pointer"
                  title="Supprimer"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-3 flex items-center justify-between text-[11px] text-slate-400 flex-shrink-0">
          <span className="flex items-center gap-1 text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" /> Chiffrement AES-256 actif
          </span>
          <button
            onClick={closeModal}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-semibold cursor-pointer"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};
