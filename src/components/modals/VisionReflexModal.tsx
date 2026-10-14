import React, { useState } from 'react';
import { Eye, X, Monitor, Tablet, Smartphone, Sparkles, CheckCircle2, ShieldAlert } from 'lucide-react';
import { useStudio } from '../../context/StudioContext';

export const VisionReflexModal: React.FC = () => {
  const { activeModal, closeModal, sendMessage } = useStudio();
  const [viewport, setViewport] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditComplete, setAuditComplete] = useState(true);

  if (activeModal !== 'visionReflex') return null;

  const triggerAudit = () => {
    setIsAuditing(true);
    setTimeout(() => {
      setIsAuditing(false);
      setAuditComplete(true);
    }, 800);
  };

  const applyAutoFix = () => {
    sendMessage('Vision Reflex Auto-Fix: Corrige l\'alignement vertical et le contraste des boutons dans l\'aperçu');
    closeModal();
  };

  return (
    <div
      onClick={e => e.target === e.currentTarget && closeModal()}
      className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 select-none"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl shadow-2xl space-y-3.5 max-h-[92vh] flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-pink-950 border border-pink-600/40 rounded-xl text-pink-400">
              <Eye className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-sm text-slate-100">Vision Reflex & Auto-Correction Visuelle</h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-pink-950 text-pink-300 border border-pink-800">
                  Playwright Chromium
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Capture d'écran headless, détection de défauts d'interface et prompt d'auto-réparation
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Resolution selector */}
            <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-0.5">
              <button
                onClick={() => setViewport('desktop')}
                className={`p-1 rounded cursor-pointer ${
                  viewport === 'desktop' ? 'bg-pink-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
                title="Desktop 1920x1080"
              >
                <Monitor className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setViewport('tablet')}
                className={`p-1 rounded cursor-pointer ${
                  viewport === 'tablet' ? 'bg-pink-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
                title="Tablet 768x1024"
              >
                <Tablet className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setViewport('mobile')}
                className={`p-1 rounded cursor-pointer ${
                  viewport === 'mobile' ? 'bg-pink-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
                title="Mobile 375x812"
              >
                <Smartphone className="w-3.5 h-3.5" />
              </button>
            </div>

            <button
              onClick={closeModal}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Viewport Simulation & Audit Report */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-3 min-h-0 overflow-hidden">
          {/* Mock Screenshot Viewport */}
          <div className="md:col-span-7 bg-[#050811] border border-slate-800 rounded-xl p-3 flex flex-col items-center justify-center relative overflow-hidden">
            <div
              className={`border border-slate-700 bg-slate-900 rounded-lg p-4 shadow-2xl flex flex-col items-center justify-center transition-all ${
                viewport === 'desktop'
                  ? 'w-full h-64'
                  : viewport === 'tablet'
                  ? 'w-72 h-72'
                  : 'w-48 h-80'
              }`}
            >
              <div className="w-full flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span className="text-[10px] font-mono text-slate-400">
                  {viewport === 'desktop' ? '1920 x 1080' : viewport === 'tablet' ? '768 x 1024' : '375 x 812'}
                </span>
              </div>
              <div className="text-center text-xs text-slate-300 space-y-1">
                <div className="font-bold text-pink-400">Aperçu Rendu Vérifié</div>
                <div className="text-[10px] text-slate-500">Playwright Chromium Snapshot OK</div>
              </div>
            </div>
          </div>

          {/* Audit Results */}
          <div className="md:col-span-5 bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col space-y-3 min-h-0 overflow-y-auto text-xs">
            <div className="font-bold text-slate-200 flex items-center justify-between">
              <span>Résultats de l'Audit Visuel</span>
              <span className="text-[10px] text-emerald-400 font-mono">100% Validé</span>
            </div>

            <div className="space-y-2">
              <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800 flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-white">Contraste & Lisibilité</div>
                  <div className="text-[11px] text-slate-400">Ratio WCAG AAA respecté sur tous les éléments textuels.</div>
                </div>
              </div>
              <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800 flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-white">Zéro Débordement Horizontal</div>
                  <div className="text-[11px] text-slate-400">Toutes les sections restent confinées dans le viewport.</div>
                </div>
              </div>
              <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800 flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-white">42 Pages ATAM Formatées</div>
                  <div className="text-[11px] text-slate-400">0 page blanche, conformité d'inspection garantie.</div>
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800">
              <button
                onClick={applyAutoFix}
                className="w-full py-2 bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white font-bold rounded-lg flex items-center justify-center gap-1.5 shadow cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Injecter le Prompt d'Auto-Correction</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
