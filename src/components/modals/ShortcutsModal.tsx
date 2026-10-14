import React from 'react';
import { HelpCircle, X } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const ShortcutsModal: React.FC = () => {
  const { activeModal, closeModal } = useStudio();

  if (activeModal !== 'shortcuts') return null;

  const shortcuts = [
    { key: 'Ctrl + K', desc: 'Ouvrir la palette de commandes globale' },
    { key: 'Ctrl + B', desc: 'Afficher / Masquer le volet gauche d\'outils et de fichiers' },
    { key: 'Ctrl + J', desc: 'Afficher / Masquer le panneau d\'aperçu réel à droite' },
    { key: 'Ctrl + `', desc: 'Basculer le terminal interactif PowerShell (PTY)' },
    { key: 'Ctrl + Enter', desc: 'Envoyer l\'instruction dans le chat' },
    { key: 'Shift + Enter', desc: 'Insérer un saut de ligne dans le prompt' },
    { key: 'Ctrl + S', desc: 'Sauvegarder le fichier en cours dans l\'éditeur Monaco' },
    { key: 'Esc', desc: 'Fermer la modal ou le panneau actif' }
  ];

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-5 shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-sky-400" />
            <h2 className="font-bold text-sm text-slate-100">Raccourcis Clavier (Agy Studio)</h2>
          </div>
          <button
            onClick={closeModal}
            className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Shortcuts list */}
        <div className="space-y-2 text-xs">
          {shortcuts.map(s => (
            <div
              key={s.key}
              className="p-2 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between"
            >
              <span className="text-slate-300">{s.desc}</span>
              <kbd className="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-sky-400 font-mono text-[11px] font-bold">
                {s.key}
              </kbd>
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
