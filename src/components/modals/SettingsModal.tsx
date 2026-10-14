import React from 'react';
import { Settings, X, Shield, Terminal, Database, Save, RotateCcw } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const SettingsModal: React.FC = () => {
  const {
    activeModal,
    closeModal,
    workspacePath,
    setWorkspacePath,
    currentModel,
    language,
    setLanguage
  } = useStudio();

  if (activeModal !== 'settings') return null;

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-5 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-slate-800 rounded-xl text-slate-300">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-100">
                Paramètres Système & Intelligence (v2.6)
              </h2>
              <p className="text-[11px] text-slate-400">
                Configuration de l'environnement d'exécution Windows, des modèles et du pont local
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

        {/* Settings Body */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
          {/* Workspace path */}
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
            <label className="font-bold text-slate-200 block">Répertoire de Travail Actif</label>
            <input
              type="text"
              value={workspacePath}
              onChange={e => setWorkspacePath(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 font-mono outline-none focus:border-sky-500"
            />
            <span className="text-[10px] text-slate-500">
              Utilisé par agy CLI pour la résolution de fichiers et l'exécution de commandes.
            </span>
          </div>

          {/* Native bridge info */}
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-200">Pont WinForms (Port 8001)</span>
              <span className="text-[10px] font-mono text-emerald-400 font-bold">● Écoute active</span>
            </div>
            <p className="text-[11px] text-slate-400">
              AgyStudioFolderPicker.exe permet l'ouverture native du dialogue Windows FolderBrowserDialog en contournant les restrictions de conteneur.
            </p>
          </div>

          {/* Langue */}
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
            <span className="font-bold text-slate-200 block">Langue de l'Interface</span>
            <div className="flex gap-2">
              <button
                onClick={() => setLanguage('fr')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                  language === 'fr' ? 'bg-indigo-600 text-white shadow' : 'bg-slate-900 text-slate-400'
                }`}
              >
                Français (Défaut)
              </button>
              <button
                onClick={() => setLanguage('en')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                  language === 'en' ? 'bg-indigo-600 text-white shadow' : 'bg-slate-900 text-slate-400'
                }`}
              >
                English
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-3 flex justify-end">
          <button
            onClick={closeModal}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold cursor-pointer"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};
