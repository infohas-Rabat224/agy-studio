import React, { useState, useRef, useEffect } from 'react';
import {
  RotateCcw,
  Sparkles,
  GraduationCap,
  Gauge,
  Cpu,
  Eye,
  Terminal,
  Paperclip,
  Clipboard,
  Mic,
  Send,
  CornerDownLeft,
  Zap,
  Brain,
  AlertTriangle,
  CheckCircle,
  Copy,
  Check,
  Search,
  X,
  ArrowUp,
  ArrowDown
} from 'lucide-react';
import { useStudio } from '../context/StudioContext';
import { ChatMessage } from '../types';

export const ChatArea: React.FC = () => {
  const {
    currentMode,
    currentAgent,
    agents,
    currentModel,
    thinkingMode,
    setThinkingMode,
    messages,
    sendMessage,
    isSending,
    clearMessages,
    openModal,
    approvalBanner,
    setApprovalBanner
  } = useStudio();

  const [inputPrompt, setInputPrompt] = useState('');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);

  // Search state
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleSend = () => {
    if (!inputPrompt.trim() && attachments.length === 0) return;
    sendMessage(inputPrompt, attachments);
    setInputPrompt('');
    setAttachments([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files).map(f => f.name);
      setAttachments(prev => [...prev, ...files]);
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const pasteFromClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setInputPrompt(prev => prev + (prev ? '\n' : '') + text);
      }
    } catch {
      // Fallback
    }
  };

  const toggleVoiceDictation = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('La reconnaissance vocale Web Speech API n\'est pas supportée sur ce navigateur.');
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'fr-FR';
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => setIsListening(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputPrompt(prev => prev + (prev ? ' ' : '') + transcript);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);

      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  // Filter messages based on search query
  const filteredMessages = searchQuery.trim()
    ? messages.filter(m => m.text.toLowerCase().includes(searchQuery.toLowerCase()))
    : messages;

  return (
    <main className="flex-1 flex flex-col bg-slate-950/40 min-w-0 h-full overflow-hidden">
      {/* MODE CONTEXT CHIPS BAR */}
      <div className="px-3 py-1.5 border-b border-slate-800/60 bg-slate-900/20 flex items-center justify-between gap-2 overflow-x-auto text-xs flex-shrink-0 select-none">
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setInputPrompt('/plan ')}
            className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-sky-400 font-mono rounded text-[11px] border border-slate-800 flex items-center gap-1 transition cursor-pointer"
          >
            <span>/plan</span>
          </button>
          <button
            onClick={() => setInputPrompt('/quota ')}
            className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-emerald-400 font-mono rounded text-[11px] border border-slate-800 flex items-center gap-1 transition cursor-pointer"
          >
            <span>/quota</span>
          </button>
          <button
            onClick={() => setInputPrompt('/boost ')}
            className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-indigo-400 font-mono rounded text-[11px] border border-slate-800 flex items-center gap-1 transition cursor-pointer"
          >
            <span>/boost</span>
          </button>
          <button
            onClick={() => setInputPrompt('Refactorise ce code avec architecture propre et typage strict')}
            className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded text-[11px] border border-slate-800 transition cursor-pointer"
          >
            Refactoriser
          </button>
          <button
            onClick={() => setInputPrompt('Génère les tests de non-régression et vérifie la couverture')}
            className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded text-[11px] border border-slate-800 transition cursor-pointer"
          >
            Tests & Non-Régression
          </button>
          <button
            onClick={() => setShowSearch(!showSearch)}
            className="px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white rounded text-[11px] border border-slate-800 transition cursor-pointer flex items-center gap-1"
          >
            <Search className="w-3 h-3" />
            <span>Rechercher</span>
          </button>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={clearMessages}
            title="Archiver le contexte et remettre les tokens à zéro"
            className="px-2 py-0.5 bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 font-semibold text-[10px] rounded border border-rose-800/50 flex items-center gap-1 transition cursor-pointer"
          >
            <RotateCcw className="w-3 h-3 text-rose-400" /> Nouveau Fil
          </button>
        </div>
      </div>

      {/* SEARCH BAR (COLLAPSIBLE) */}
      {showSearch && (
        <div className="px-4 py-2 bg-slate-900 border-b border-slate-800 flex items-center gap-2 flex-shrink-0">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Rechercher dans les messages..."
            className="flex-1 bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-xs text-white placeholder-slate-500 outline-none focus:border-sky-500"
            autoFocus
          />
          <span className="text-xs text-slate-400">
            {filteredMessages.length} résultat{filteredMessages.length > 1 ? 's' : ''}
          </span>
          <button
            onClick={() => {
              setShowSearch(false);
              setSearchQuery('');
            }}
            className="p-1 text-slate-400 hover:text-white cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* MESSAGES SCROLL AREA */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 select-text">
        {/* Welcome Card */}
        <div className="bg-gradient-to-r from-slate-900/90 to-slate-900/60 border border-slate-800/80 rounded-2xl p-5 shadow-lg space-y-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-sky-500/10 rounded-xl text-sky-400 border border-sky-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-100">
                Agy Studio Débridé — Antigravity Agentic Suite v2.6
              </h3>
              <p className="text-xs text-slate-400">
                Toutes les fonctions du terminal agy CLI et des 130+ compétences sont connectées en direct.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs pt-1">
            <div
              onClick={() => openModal('visionReflex')}
              className="p-2.5 bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800/80 rounded-xl cursor-pointer transition"
            >
              <div className="font-semibold text-amber-400 flex items-center gap-1.5">
                <GraduationCap className="w-3.5 h-3.5" /> 7 Formateurs Validés
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">42 pages chacun, DOCX + PDF, 0 page blanche.</div>
            </div>
            <div
              onClick={() => openModal('quota')}
              className="p-2.5 bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800/80 rounded-xl cursor-pointer transition"
            >
              <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <Gauge className="w-3.5 h-3.5" /> Quotas Directs
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Commandes /quota connectées aux jauges réelles.</div>
            </div>
            <div
              onClick={() => openModal('model')}
              className="p-2.5 bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800/80 rounded-xl cursor-pointer transition"
            >
              <div className="font-semibold text-sky-400 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> Multi-Modèles
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Gemini 3.8 Flash, 3.1 Pro, Claude Sonnet 3.7.</div>
            </div>
            <div
              onClick={() => openModal('monaco')}
              className="p-2.5 bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800/80 rounded-xl cursor-pointer transition"
            >
              <div className="font-semibold text-indigo-400 flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5" /> Monaco & Split Diff
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Édition en direct, visualisation des modifications.</div>
            </div>
          </div>
        </div>

        {/* Message Items */}
        {filteredMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col space-y-1.5 ${
              msg.sender === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            {/* Header info */}
            <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono px-1">
              <span className="font-semibold text-slate-300">
                {msg.sender === 'user' ? 'Développeur' : msg.agentName || 'Antigravity'}
              </span>
              <span>•</span>
              <span>{msg.timestamp}</span>
              {msg.tokens && (
                <>
                  <span>•</span>
                  <span className="text-sky-400">{msg.tokens} tokens</span>
                </>
              )}
              {msg.latencyMs && (
                <>
                  <span>•</span>
                  <span className="text-emerald-400">{msg.latencyMs}ms</span>
                </>
              )}
            </div>

            {/* Content Bubble */}
            <div
              className={`p-3.5 rounded-2xl max-w-2xl text-xs leading-relaxed space-y-2 select-text ${
                msg.sender === 'user'
                  ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-br-xs shadow-md'
                  : 'bg-slate-900 border border-slate-800/90 text-slate-200 rounded-bl-xs shadow-md'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.text}</div>

              {/* Attachments preview */}
              {msg.attachments && msg.attachments.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {msg.attachments.map((att, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] bg-slate-950/70 border border-slate-700/80 px-2 py-0.5 rounded-md text-sky-300 font-mono flex items-center gap-1"
                    >
                      <Paperclip className="w-3 h-3 text-sky-400" />
                      {att}
                    </span>
                  ))}
                </div>
              )}

              {/* Tool Execution Block */}
              {msg.toolExecution && (
                <div className="mt-2.5 pt-2 border-t border-slate-800 bg-slate-950/90 rounded-xl p-2.5 font-mono text-[11px] space-y-1.5">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
                      <Terminal className="w-3 h-3" />
                      {msg.toolExecution.toolName}
                    </span>
                    <button
                      onClick={() => copyToClipboard(msg.toolExecution?.output || '', msg.id)}
                      className="hover:text-white transition flex items-center gap-1 cursor-pointer"
                    >
                      {copiedId === msg.id ? (
                        <Check className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <Copy className="w-3 h-3 text-slate-500" />
                      )}
                      <span>Copier</span>
                    </button>
                  </div>
                  {msg.toolExecution.command && (
                    <div className="text-sky-300 text-[10px]">
                      $ {msg.toolExecution.command}
                    </div>
                  )}
                  {msg.toolExecution.output && (
                    <pre className="text-slate-300 bg-[#060911] p-2 rounded border border-slate-900 max-h-36 overflow-y-auto whitespace-pre-wrap text-[10px]">
                      {msg.toolExecution.output}
                    </pre>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {isSending && (
          <div className="flex items-center gap-2 text-xs text-sky-400 font-mono p-2">
            <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping"></span>
            <span>{agents.find(a => a.id === currentAgent)?.name} réfléchit et exécute...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* APPROVAL CONFIRMATION BANNER */}
      {approvalBanner && approvalBanner.open && (
        <div className="p-3 bg-rose-950/80 border-t border-rose-800 text-xs flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <div>
              <div className="font-bold text-rose-200">Validation requise (HITL Gate)</div>
              <div className="font-mono text-[11px] text-rose-300 truncate max-w-lg">
                {approvalBanner.command}
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setApprovalBanner(null)}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-medium cursor-pointer"
            >
              Annuler
            </button>
            <button
              onClick={() => {
                sendMessage(`Autorisé : ${approvalBanner.command}`);
                setApprovalBanner(null);
              }}
              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-semibold text-xs cursor-pointer shadow"
            >
              Exécuter
            </button>
          </div>
        </div>
      )}

      {/* DRAG & DROP ATTACHMENT + PROMPT INPUT */}
      <div className="p-3 bg-slate-950/90 border-t border-slate-800/80 backdrop-blur space-y-2 flex-shrink-0">
        {/* Thinking Mode & Session Quota Toolbar */}
        <div className="flex items-center justify-between text-[11px] px-0.5 select-none">
          <div className="inline-flex p-0.5 bg-slate-900 border border-slate-800 rounded-lg">
            <button
              onClick={() => setThinkingMode('turbo')}
              title="Exécution directe ultra-rapide (Modèle Flash, 0 gaspillage de quota)"
              className={`px-2.5 py-1 rounded-md font-semibold transition flex items-center gap-1.5 text-[11px] cursor-pointer ${
                thinkingMode === 'turbo'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Zap className="w-3.5 h-3.5 text-amber-300" /> Turbo Flash (Eco Quota)
            </button>
            <button
              onClick={() => setThinkingMode('deep')}
              title="Raisonnement poussé multi-étapes avec effort élevé"
              className={`px-2.5 py-1 rounded-md font-semibold transition flex items-center gap-1.5 text-[11px] cursor-pointer ${
                thinkingMode === 'deep'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Brain className="w-3.5 h-3.5 text-indigo-400" /> Deep Reasoning (Claude / Pro)
            </button>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
            <span>
              Tokens estimés : <strong className="text-sky-400 font-bold">{Math.max(inputPrompt.length * 2, 0)}</strong>
            </span>
          </div>
        </div>

        {/* Attached Files Badges */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {attachments.map((att, idx) => (
              <span
                key={idx}
                className="text-[10px] bg-slate-900 border border-slate-700 px-2 py-0.5 rounded-md text-sky-300 font-mono flex items-center gap-1.5"
              >
                <Paperclip className="w-3 h-3 text-sky-400" />
                <span>{att}</span>
                <button
                  onClick={() => removeAttachment(idx)}
                  className="hover:text-rose-400 cursor-pointer ml-1"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        <div className="relative flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1.5 focus-within:border-sky-500 transition shadow-inner">
          {/* Attachment Button */}
          <label
            className="p-2 text-slate-400 hover:text-sky-400 cursor-pointer rounded-lg hover:bg-slate-800 transition"
            title="Joindre des fichiers (Images, PDF, Word, Excel, PPT, Code)"
          >
            <input
              type="file"
              multiple
              className="hidden"
              onChange={handleFileUpload}
            />
            <Paperclip className="w-4 h-4" />
          </label>

          {/* Windows Native Clipboard Paste Button */}
          <button
            type="button"
            onClick={pasteFromClipboard}
            title="Coller depuis le presse-papier Windows (Ctrl+V)"
            className="p-2 text-slate-400 hover:text-emerald-400 cursor-pointer rounded-lg hover:bg-slate-800 transition"
          >
            <Clipboard className="w-4 h-4" />
          </button>

          {/* Voice Dictation Button */}
          <button
            type="button"
            onClick={toggleVoiceDictation}
            title="Dictée vocale directe"
            className={`p-2 cursor-pointer rounded-lg hover:bg-slate-800 transition ${
              isListening ? 'text-rose-400 bg-rose-950/50 animate-pulse' : 'text-slate-400 hover:text-rose-400'
            }`}
          >
            <Mic className="w-4 h-4" />
          </button>

          <textarea
            value={inputPrompt}
            onChange={e => setInputPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            placeholder="Tapez une instruction, une commande (/quota, /model, /plan) ou dictez vocalement..."
            className="w-full bg-transparent border-0 text-xs text-slate-200 placeholder-slate-500 focus:outline-none resize-none px-2 py-1 leading-relaxed"
          />

          <button
            onClick={handleSend}
            disabled={!inputPrompt.trim() && attachments.length === 0}
            className="p-2.5 rounded-lg bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 disabled:opacity-40 text-white font-medium flex-shrink-0 shadow-md shadow-sky-500/20 transition cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center justify-between px-1 pt-0.5 text-[10px] text-slate-500 select-none">
          <span className="flex items-center gap-1 font-mono">
            <CornerDownLeft className="w-3 h-3 text-slate-600" /> Entrée pour envoyer, Maj + Entrée pour saut de ligne
          </span>
          <span className="text-slate-400 font-mono">
            Autorisation : <strong className="text-emerald-400">Permanente</strong> | Modèle :{' '}
            <strong
              onClick={() => openModal('model')}
              className="text-sky-400 cursor-pointer hover:underline hover:text-white"
            >
              {currentModel}
            </strong>
          </span>
        </div>
      </div>
    </main>
  );
};
