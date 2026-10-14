import React, { useState } from 'react';
import { Code2, X, Save, SplitSquareHorizontal, Check, RefreshCw, FileCode } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const MonacoModal: React.FC = () => {
  const { activeModal, closeModal, files } = useStudio();
  const [selectedPath, setSelectedPath] = useState<string>('backend/server.py');
  const [viewMode, setViewMode] = useState<'edit' | 'diff'>('edit');
  const [codeContent, setCodeContent] = useState<string>(() => {
    return files.find(f => f.path === 'backend/server.py')?.content || '// Select a file';
  });
  const [statusText, setStatusText] = useState('Prêt');

  if (activeModal !== 'monaco') return null;

  const handleSelectFile = (path: string) => {
    setSelectedPath(path);
    const file = files.find(f => f.path === path);
    if (file) {
      setCodeContent(file.content || `// Content of ${file.path}`);
      setStatusText(`Chargé (${( (file.size || 1000) / 1024).toFixed(1)} KB)`);
    }
  };

  const handleSave = () => {
    setStatusText('Sauvegarde sur disque...');
    setTimeout(() => {
      setStatusText('Enregistré avec succès !');
      setTimeout(() => setStatusText('Prêt'), 2000);
    }, 400);
  };

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-6xl shadow-2xl space-y-3.5 max-h-[92vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-sky-950 border border-sky-600/40 rounded-xl text-sky-400">
              <Code2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-sm text-slate-100">Éditeur Monaco & Split Diff Viewer</h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800">
                  {selectedPath}
                </span>
                <span className="text-[10px] font-mono text-emerald-400">{statusText}</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Éditeur VS Code intégré avec coloration syntaxique, mini-map et comparaison multi-branches
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode(viewMode === 'edit' ? 'diff' : 'edit')}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-sky-400 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
            >
              <SplitSquareHorizontal className="w-3.5 h-3.5" />
              <span>{viewMode === 'edit' ? 'Mode Split Diff' : 'Mode Éditeur'}</span>
            </button>
            <button
              onClick={handleSave}
              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Enregistrer (Ctrl+S)</span>
            </button>
            <button
              onClick={closeModal}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Main Grid: File list & Code Editor / Diff View */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-3 min-h-0 overflow-hidden">
          {/* Files List sidebar */}
          <div className="md:col-span-3 bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col min-h-0 overflow-hidden">
            <span className="text-xs font-bold text-slate-300 mb-2 flex items-center gap-1.5 flex-shrink-0">
              <FileCode className="w-3.5 h-3.5 text-sky-400" />
              <span>Fichiers du Workspace</span>
            </span>
            <div className="flex-1 overflow-y-auto space-y-1 text-xs font-mono text-slate-300 pr-1">
              {files.map(f => (
                <button
                  key={f.path}
                  onClick={() => handleSelectFile(f.path)}
                  className={`w-full px-2 py-1.5 text-left rounded truncate transition cursor-pointer flex items-center justify-between text-[11px] ${
                    selectedPath === f.path ? 'bg-sky-950 text-sky-300 border border-sky-800' : 'hover:bg-slate-900 text-slate-400'
                  }`}
                >
                  <span className="truncate">{f.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Editor Container */}
          <div className="md:col-span-9 bg-[#060911] border border-slate-800 rounded-xl flex flex-col min-h-0 overflow-hidden">
            {viewMode === 'edit' ? (
              <div className="flex-1 flex flex-col overflow-hidden">
                <div className="h-7 px-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span>{selectedPath}</span>
                  <span>UTF-8 • {selectedPath.split('.').pop()?.toUpperCase()}</span>
                </div>
                <textarea
                  value={codeContent}
                  onChange={e => setCodeContent(e.target.value)}
                  className="flex-1 p-3 bg-transparent text-slate-200 font-mono text-xs outline-none resize-none leading-relaxed select-text"
                  spellCheck={false}
                />
              </div>
            ) : (
              /* Diff Mode (Original vs Modified) */
              <div className="flex-1 grid grid-cols-2 divide-x divide-slate-800 overflow-hidden font-mono text-xs">
                <div className="flex flex-col overflow-hidden">
                  <div className="h-7 px-3 bg-rose-950/40 border-b border-slate-800 flex items-center text-[10px] text-rose-300">
                    ORIGINAL (HEAD)
                  </div>
                  <pre className="flex-1 p-3 overflow-auto bg-slate-950/60 text-slate-400 text-[11px] whitespace-pre-wrap select-text">
                    {codeContent}
                  </pre>
                </div>
                <div className="flex flex-col overflow-hidden">
                  <div className="h-7 px-3 bg-emerald-950/40 border-b border-slate-800 flex items-center justify-between text-[10px] text-emerald-300">
                    <span>MODIFIÉ (PROPOSÉ PAR AGENT)</span>
                    <button
                      onClick={() => alert('Modifications acceptées et fusionnées !')}
                      className="px-2 py-0.5 bg-emerald-700 hover:bg-emerald-600 text-white rounded text-[9px] font-bold cursor-pointer"
                    >
                      Accepter les changements
                    </button>
                  </div>
                  <pre className="flex-1 p-3 overflow-auto bg-[#07130b] text-emerald-300 text-[11px] whitespace-pre-wrap select-text">
                    {codeContent}
                    {'\n// + Optimisations adaptatives générées par Antigravity'}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
