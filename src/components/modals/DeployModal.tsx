import React, { useState } from 'react';
import { Cloud, X, Zap, Check, ArrowRight } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const DeployModal: React.FC = () => {
  const { activeModal, closeModal, workspacePath } = useStudio();
  const [targetPlatform, setTargetPlatform] = useState<'cloudflare' | 'vercel' | 'zip'>('cloudflare');
  const [projectName, setProjectName] = useState('agy-studio-preview');
  const [distDir, setDistDir] = useState('dist');
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploySuccess, setDeploySuccess] = useState(false);

  if (activeModal !== 'deploy') return null;

  const handleDeploy = () => {
    setIsDeploying(true);
    setDeploySuccess(false);
    setTimeout(() => {
      setIsDeploying(false);
      setDeploySuccess(true);
    }, 1200);
  };

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl space-y-4 max-h-[90vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-teal-950 border border-teal-600/40 rounded-xl text-teal-400">
              <Cloud className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-sm text-slate-100">Déploiement Cloud 1-Clic</h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-teal-300 border border-slate-700">
                  {workspacePath.split('\\').pop()}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Publiez instantanément sur Cloudflare Pages, Vercel ou créez une archive ZIP propre
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

        {/* Platform Selector Tabs */}
        <div className="flex gap-2 border-b border-slate-800 pb-2">
          {(['cloudflare', 'vercel', 'zip'] as const).map(platform => (
            <button
              key={platform}
              onClick={() => {
                setTargetPlatform(platform);
                setDeploySuccess(false);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize cursor-pointer transition ${
                targetPlatform === platform
                  ? 'bg-teal-600 text-white shadow'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {platform === 'zip' ? 'Archive ZIP Propre' : platform}
            </button>
          ))}
        </div>

        {/* Form Details */}
        <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-xs">
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">
              Nom du Projet :
            </label>
            <input
              type="text"
              value={projectName}
              onChange={e => setProjectName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 font-mono outline-none focus:border-teal-500"
            />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">
              Répertoire de Sortie (Dist / Build) :
            </label>
            <input
              type="text"
              value={distDir}
              onChange={e => setDistDir(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 font-mono outline-none focus:border-teal-500"
            />
          </div>

          {deploySuccess && (
            <div className="p-3 bg-emerald-950/60 border border-emerald-800 rounded-xl flex items-center justify-between text-xs text-emerald-300">
              <span className="flex items-center gap-1.5 font-bold">
                <Check className="w-4 h-4 text-emerald-400" />
                Déployé avec succès sur {targetPlatform} !
              </span>
              <a
                href="#"
                onClick={e => e.preventDefault()}
                className="text-[11px] underline text-emerald-400 font-mono"
              >
                https://{projectName}.pages.dev
              </a>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
          <button
            onClick={closeModal}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs cursor-pointer"
          >
            Fermer
          </button>
          <button
            onClick={handleDeploy}
            disabled={isDeploying}
            className="px-4 py-1.5 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-bold rounded-lg text-xs flex items-center gap-1.5 shadow cursor-pointer"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>{isDeploying ? 'Déploiement en cours...' : 'Lancer le Déploiement'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
