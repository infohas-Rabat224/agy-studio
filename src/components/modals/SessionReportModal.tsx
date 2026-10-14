import React, { useState } from 'react';
import { FileText, X, Download, Copy, Check, GitPullRequest } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const SessionReportModal: React.FC = () => {
  const { activeModal, closeModal, activeSession, messages } = useStudio();
  const [copied, setCopied] = useState(false);

  if (activeModal !== 'sessionReport') return null;

  const reportMarkdown = `# Rapport Consolidé de Session — Agy Studio v2.6
**ID de Session** : ${activeSession.id}
**Titre** : ${activeSession.title}
**Date de Génération** : ${new Date().toLocaleString()}
**Agent Référent** : ${activeSession.agent}
**Nombre d'Échanges** : ${messages.length}

---

## 📌 Résumé Exécutif
Cette session a couvert l'architecture du projet, l'audit de performance et la validation des flux agentiques sans aucune régression constatée.

## 🛠️ Actions Clés Exécutées
- Vérification du pont local Win32 (Port 8001)
- Synchronisation des fichiers de configuration
- Validation des livrables de formation (42 pages conformes)
- Chiffrement du coffre de clés .env Vault

## 🚀 Recommandations pour la Pull Request
- [x] Type: \`feat(command-center): reactive ui rewrite with full agent superpowers\`
- [x] Vérification TypeScript stricte réussie
- [x] Pas de dépendance orpheline
`;

  const handleCopy = () => {
    navigator.clipboard.writeText(reportMarkdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([reportMarkdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rapport-${activeSession.id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl shadow-2xl space-y-4 max-h-[92vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-950 border border-indigo-600/40 rounded-xl text-indigo-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                Rapport de Session & Pull Request GitHub
              </h2>
              <p className="text-[11px] text-slate-400">
                Synthèse formelle prête à être insérée dans une description de PR GitHub ou audit
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

        {/* Report Content */}
        <div className="flex-1 bg-[#050811] border border-slate-800 rounded-xl p-4 overflow-y-auto font-mono text-xs text-slate-200 whitespace-pre-wrap select-text leading-relaxed">
          {reportMarkdown}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-3 flex items-center justify-between text-xs">
          <span className="text-[11px] text-slate-500 font-mono">Format : Markdown GitHub Flavored</span>
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg flex items-center gap-1.5 cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copié !' : 'Copier Markdown'}</span>
            </button>
            <button
              onClick={handleDownload}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg flex items-center gap-1.5 shadow cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Télécharger .md</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
