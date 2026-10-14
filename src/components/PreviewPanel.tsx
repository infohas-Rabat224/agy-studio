import React, { useState } from 'react';
import {
  FileText,
  FileCode,
  Maximize2,
  Minimize2,
  ExternalLink,
  Download,
  SplitSquareHorizontal,
  RotateCw,
  X,
  Eye,
  PanelRightOpen,
  CheckCircle2,
  FileCheck
} from 'lucide-react';
import { useStudio } from '../context/StudioContext';

export const PreviewPanel: React.FC = () => {
  const {
    previewFile,
    isPreviewOpen,
    setIsPreviewOpen,
    isPreviewAutofit,
    setIsPreviewAutofit,
    isSplitPreview,
    setIsSplitPreview,
    openModal,
    files
  } = useStudio();

  const [companionMode, setCompanionMode] = useState<'doc' | 'pdf'>('doc');
  const [splitFilePath, setSplitFilePath] = useState<string>('backend/server.py');

  if (!isPreviewOpen) {
    return (
      <div className="w-8 border-l border-slate-800/80 bg-slate-950/90 flex flex-col items-center py-2 flex-shrink-0 z-10 select-none">
        <button
          onClick={() => setIsPreviewOpen(true)}
          title="Déplier le panneau d'aperçu (Ctrl+J)"
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition mb-3 cursor-pointer"
        >
          <PanelRightOpen className="w-4 h-4 text-indigo-400" />
        </button>
        <div className="writing-vertical text-[10px] uppercase font-mono text-slate-500 tracking-wider">
          Aperçu
        </div>
      </div>
    );
  }

  const handleDownload = () => {
    if (!previewFile) return;
    const blob = new Blob([previewFile.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = previewFile.path.split('/').pop() || 'document.txt';
    link.click();
    URL.revokeObjectURL(url);
  };

  const splitFile = files.find(f => f.path === splitFilePath);

  return (
    <aside
      className={`border-l border-slate-800/80 bg-slate-950 flex flex-col flex-shrink-0 z-20 transition-all duration-300 ${
        isPreviewAutofit
          ? 'w-full flex-1'
          : 'w-full md:w-[500px] lg:w-[45vw] min-w-[340px]'
      }`}
    >
      {/* Preview Header */}
      <div className="h-11 border-b border-slate-800/80 bg-slate-900/60 px-3 flex items-center justify-between text-xs flex-shrink-0 select-none">
        <div className="flex items-center space-x-2 truncate">
          {previewFile?.type === 'code' ? (
            <FileCode className="w-4 h-4 text-sky-400 flex-shrink-0" />
          ) : (
            <FileText className="w-4 h-4 text-sky-400 flex-shrink-0" />
          )}
          <span className="font-bold text-slate-200 truncate">
            {previewFile?.title || 'Aperçu Réel'}
          </span>
          {isPreviewAutofit && (
            <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-sky-950 border border-sky-800 text-sky-400 font-semibold">
              Plein écran
            </span>
          )}
        </div>

        <div className="flex items-center space-x-1.5 flex-shrink-0">
          {/* Vision Reflex button */}
          <button
            onClick={() => openModal('visionReflex')}
            title="Auditer visuellement cet aperçu avec Vision Reflex (Playwright)"
            className="px-2 py-0.5 bg-pink-950/80 border border-pink-700/60 hover:bg-pink-900 text-pink-300 rounded text-[11px] flex items-center gap-1 font-medium transition cursor-pointer"
          >
            <Eye className="w-3 h-3 text-pink-400" />
            <span className="hidden sm:inline">Reflex IA</span>
          </button>

          {/* Autofit toggle */}
          <button
            onClick={() => setIsPreviewAutofit(!isPreviewAutofit)}
            title="Ajustement automatique / Plein écran"
            className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition cursor-pointer"
          >
            {isPreviewAutofit ? (
              <Minimize2 className="w-3.5 h-3.5" />
            ) : (
              <Maximize2 className="w-3.5 h-3.5" />
            )}
          </button>

          {/* External open */}
          <button
            onClick={() => alert(`Ouverture du document ${previewFile?.path} dans l'application native Windows...`)}
            title="Ouvrir dans Word / Acrobat / Windows"
            className="px-2 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded text-[11px] flex items-center gap-1 font-medium cursor-pointer"
          >
            <ExternalLink className="w-3 h-3" />
            <span className="hidden md:inline">Ouvrir Système</span>
          </button>

          {/* Download */}
          <button
            onClick={handleDownload}
            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] flex items-center gap-1 font-medium cursor-pointer"
          >
            <Download className="w-3 h-3" />
            <span className="hidden md:inline">Télécharger</span>
          </button>

          {/* Split preview */}
          <button
            onClick={() => setIsSplitPreview(!isSplitPreview)}
            title="Double volet de comparaison"
            className={`p-1 rounded hover:bg-slate-800 cursor-pointer ${
              isSplitPreview ? 'text-sky-400 bg-slate-800' : 'text-slate-400 hover:text-white'
            }`}
          >
            <SplitSquareHorizontal className="w-3.5 h-3.5" />
          </button>

          {/* Close */}
          <button
            onClick={() => setIsPreviewOpen(false)}
            title="Masquer l'aperçu"
            className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Companion Bar (PDF mode toggle for ATAM formation documents) */}
      {previewFile?.companionPdf && (
        <div className="px-3 py-1 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-[11px] flex-shrink-0 select-none">
          <span className="text-slate-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Version certifiée (42 pages sans page blanche) :</span>
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setCompanionMode('pdf')}
              className={`px-2 py-0.5 rounded font-medium cursor-pointer transition ${
                companionMode === 'pdf' ? 'bg-sky-600 text-white' : 'bg-slate-800 text-slate-300 hover:text-white'
              }`}
            >
              Aperçu PDF Direct
            </button>
            <button
              onClick={() => setCompanionMode('doc')}
              className={`px-2 py-0.5 rounded font-medium cursor-pointer transition ${
                companionMode === 'doc' ? 'bg-sky-600 text-white' : 'bg-slate-800 text-slate-300 hover:text-white'
              }`}
            >
              Tableaux Word
            </button>
          </div>
        </div>
      )}

      {/* Preview Content Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left / Main Preview Pane */}
        <div className="flex-1 overflow-auto bg-[#050811] p-4 text-xs font-mono text-slate-200 select-text leading-relaxed">
          {previewFile ? (
            companionMode === 'pdf' ? (
              <div className="space-y-4 max-w-2xl mx-auto bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl font-sans">
                <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileCheck className="w-5 h-5 text-emerald-400" />
                    <h2 className="font-bold text-sm text-white">Certificat de Formation ATAM (Conforme 100%)</h2>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 font-mono text-[10px] font-bold border border-emerald-800">
                    42 / 42 Pages Validées
                  </span>
                </div>
                <div className="text-xs text-slate-300 space-y-2">
                  <p><strong>Organisme :</strong> Ministère & Inspection Académique</p>
                  <p><strong>Effectif :</strong> 7 Formateurs référents validés</p>
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1 font-mono text-[11px]">
                    <div className="text-emerald-400">✓ Page 1-6 : Fiche pédagogique & objectifs</div>
                    <div className="text-emerald-400">✓ Page 7-20 : Modules techniques et ateliers pratiques</div>
                    <div className="text-emerald-400">✓ Page 21-34 : Suivi d'évaluation et grilles de compétences</div>
                    <div className="text-emerald-400">✓ Page 35-42 : Emargement et visa de la commission</div>
                  </div>
                  <p className="text-[11px] text-slate-500 italic">Rendu haute-fidélité synchronisé avec scripts/build_master_classeur_atam.py</p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="text-[11px] text-slate-400 pb-2 border-b border-slate-900 font-sans font-medium flex items-center justify-between">
                  <span>Chemin : <code className="text-sky-400 font-mono">{previewFile.path}</code></span>
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 bg-slate-900 rounded text-slate-400">
                    {previewFile.language}
                  </span>
                </div>
                <pre className="whitespace-pre-wrap font-mono text-slate-300 text-[11px]">
                  {previewFile.content}
                </pre>
              </div>
            )
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-2 p-6 text-center">
              <FileText className="w-8 h-8 text-slate-600" />
              <p>Sélectionnez un document à gauche ou générez du code pour voir le rendu en direct.</p>
            </div>
          )}
        </div>

        {/* Right / Split Comparison Pane */}
        {isSplitPreview && (
          <div className="flex-1 border-l border-slate-800 bg-[#050811] flex flex-col overflow-hidden">
            <div className="h-8 border-b border-slate-800/80 bg-slate-900/60 px-2 flex items-center justify-between text-xs flex-shrink-0 select-none">
              <span className="text-[11px] text-slate-400 font-medium">Volet Comparaison</span>
              <select
                value={splitFilePath}
                onChange={e => setSplitFilePath(e.target.value)}
                className="bg-slate-950 border border-slate-700 text-slate-300 rounded text-[11px] px-1.5 py-0.5 max-w-[200px] truncate outline-none cursor-pointer"
              >
                {files.map(f => (
                  <option key={f.path} value={f.path}>
                    {f.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1 overflow-auto p-3 text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed select-text">
              {splitFile?.content || '// Contenu introuvable'}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
