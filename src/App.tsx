import React, { useEffect } from 'react';
import { StudioProvider, useStudio } from './context/StudioContext';
import { Header } from './components/Header';
import { ActionBar } from './components/ActionBar';
import { LeftSidebar } from './components/LeftSidebar';
import { ChatArea } from './components/ChatArea';
import { PreviewPanel } from './components/PreviewPanel';
import { TerminalDrawer } from './components/TerminalDrawer';
import { StatusBar } from './components/StatusBar';

// Modals
import { MonacoModal } from './components/modals/MonacoModal';
import { GitModal } from './components/modals/GitModal';
import { AutonomyModal } from './components/modals/AutonomyModal';
import { ProjectGraphModal } from './components/modals/ProjectGraphModal';
import { VaultModal } from './components/modals/VaultModal';
import { DeployModal } from './components/modals/DeployModal';
import { VisionReflexModal } from './components/modals/VisionReflexModal';
import { KanbanModal } from './components/modals/KanbanModal';
import { TimeMachineModal } from './components/modals/TimeMachineModal';
import { IntelligenceModal } from './components/modals/IntelligenceModal';
import { MemoryModal } from './components/modals/MemoryModal';
import { ModelModal } from './components/modals/ModelModal';
import { McpModal } from './components/modals/McpModal';
import { QuotaModal } from './components/modals/QuotaModal';
import { AgentDuelModal } from './components/modals/AgentDuelModal';
import { SessionReportModal } from './components/modals/SessionReportModal';
import { SessionModal } from './components/modals/SessionModal';
import { ShortcutsModal } from './components/modals/ShortcutsModal';
import { SettingsModal } from './components/modals/SettingsModal';
import { CommandPalette } from './components/modals/CommandPalette';

const StudioMain: React.FC = () => {
  const {
    isSidebarOpen,
    setIsSidebarOpen,
    isPreviewOpen,
    setIsPreviewOpen,
    isTerminalOpen,
    setIsTerminalOpen,
    openModal,
    closeModal,
    activeModal
  } = useStudio();

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl + K -> Command Palette
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openModal('commandPalette');
      }
      // Ctrl + B -> Toggle Sidebar
      else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        setIsSidebarOpen(!isSidebarOpen);
      }
      // Ctrl + J -> Toggle Preview
      else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'j') {
        e.preventDefault();
        setIsPreviewOpen(!isPreviewOpen);
      }
      // Ctrl + ` -> Toggle Terminal
      else if ((e.ctrlKey || e.metaKey) && e.key === '`') {
        e.preventDefault();
        setIsTerminalOpen(!isTerminalOpen);
      }
      // Esc -> Close active modal
      else if (e.key === 'Escape') {
        if (activeModal) {
          e.preventDefault();
          closeModal();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSidebarOpen, isPreviewOpen, isTerminalOpen, activeModal, openModal, closeModal, setIsSidebarOpen, setIsPreviewOpen, setIsTerminalOpen]);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#0b0f19] text-slate-100 font-sans">
      {/* Header Layer 1: Global Command Bar */}
      <Header />

      {/* Header Layer 2: Contextual Action Bar */}
      <ActionBar />

      {/* Main Workspace (Left Sidebar + Center Chat Area + Right Preview Panel) */}
      <div className="flex flex-1 overflow-hidden relative">
        <LeftSidebar />
        <ChatArea />
        <PreviewPanel />
      </div>

      {/* Bottom Retractable Interactive Terminal Drawer (Ctrl+`) */}
      <TerminalDrawer />

      {/* Layer 3 Footer: Universal Status Bar */}
      <StatusBar />

      {/* Modals & Dialogs */}
      <MonacoModal />
      <GitModal />
      <AutonomyModal />
      <ProjectGraphModal />
      <VaultModal />
      <DeployModal />
      <VisionReflexModal />
      <KanbanModal />
      <TimeMachineModal />
      <IntelligenceModal />
      <MemoryModal />
      <ModelModal />
      <McpModal />
      <QuotaModal />
      <AgentDuelModal />
      <SessionReportModal />
      <SessionModal />
      <ShortcutsModal />
      <SettingsModal />
      <CommandPalette />
    </div>
  );
};

export default function App() {
  return (
    <StudioProvider>
      <StudioMain />
    </StudioProvider>
  );
}
