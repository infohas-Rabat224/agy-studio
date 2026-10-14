import React, { useState, useRef, useEffect } from 'react';
import { Terminal as TerminalIcon, X, Trash2, CornerDownLeft } from 'lucide-react';
import { useStudio } from '../context/StudioContext';

export const TerminalDrawer: React.FC = () => {
  const {
    isTerminalOpen,
    setIsTerminalOpen,
    terminalHistory,
    executeTerminalCommand,
    clearTerminal,
    workspacePath
  } = useStudio();

  const [inputCmd, setInputCmd] = useState('');
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isTerminalOpen) {
      terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [terminalHistory, isTerminalOpen]);

  if (!isTerminalOpen) return null;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (!inputCmd.trim()) return;
      if (inputCmd.trim().toLowerCase() === 'clear' || inputCmd.trim().toLowerCase() === 'cls') {
        clearTerminal();
      } else {
        executeTerminalCommand(inputCmd);
      }
      setInputCmd('');
    }
  };

  return (
    <div className="h-72 border-t-2 border-emerald-500/80 bg-[#080c14] flex flex-col z-30 shadow-2xl transition-all select-none">
      {/* Header */}
      <div className="h-8 px-3 bg-slate-900/95 border-b border-slate-800 flex items-center justify-between text-xs flex-shrink-0">
        <div className="flex items-center gap-2">
          <TerminalIcon className="w-4 h-4 text-emerald-400" />
          <span className="font-bold text-slate-200">Terminal Interactif (PowerShell)</span>
          <span className="text-[10px] bg-slate-800 text-emerald-400 border border-emerald-800/60 px-1.5 py-0.5 rounded font-mono">
            xterm.js • ANSI • PTY
          </span>
          <span className="text-[10px] text-slate-500 hidden sm:inline">(Basculer avec Ctrl+`)</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearTerminal}
            className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] transition cursor-pointer flex items-center gap-1"
          >
            <Trash2 className="w-3 h-3" />
            <span>Effacer</span>
          </button>
          <button
            onClick={() => setIsTerminalOpen(false)}
            className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Terminal Screen Body */}
      <div className="flex-1 p-3 bg-[#050811] overflow-y-auto font-mono text-[11px] text-emerald-400 leading-snug space-y-1 select-text">
        {terminalHistory.map((line, i) => (
          <div key={i} className="whitespace-pre-wrap">{line}</div>
        ))}
        <div ref={terminalEndRef} />
      </div>

      {/* Terminal Input Line */}
      <div className="h-9 px-3 bg-[#03060c] border-t border-slate-800/80 flex items-center gap-2 font-mono text-xs flex-shrink-0">
        <span className="text-sky-400 flex-shrink-0">PS &gt;</span>
        <input
          type="text"
          value={inputCmd}
          onChange={e => setInputCmd(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Exécutez une commande PowerShell (ex: dir, agy --version, git status)..."
          className="flex-1 bg-transparent border-none text-white text-xs outline-none placeholder-slate-600"
          autoFocus
        />
        <button
          onClick={() => {
            if (!inputCmd.trim()) return;
            executeTerminalCommand(inputCmd);
            setInputCmd('');
          }}
          className="text-slate-400 hover:text-emerald-400 cursor-pointer p-1"
        >
          <CornerDownLeft className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
