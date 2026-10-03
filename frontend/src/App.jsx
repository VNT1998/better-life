import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { api } from './api/client';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import WelcomeView from './components/WelcomeView';
import ChatView from './components/ChatView';
import AuthModal from './components/AuthModal';

function MainApp() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('gemma4:e4b');
  const [config, setConfig] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Load configuration and models
  useEffect(() => {
    async function loadData() {
      try {
        const [modelsData, configData] = await Promise.all([
          api.getModels().catch(() => null),
          api.getConfig().catch(() => null),
        ]);

        if (modelsData) {
          const avail = modelsData.available_models || [];
          setModels(avail);
          if (modelsData.primary_model) {
            setSelectedModel(modelsData.primary_model);
          } else if (avail.length > 0) {
            setSelectedModel(avail[0].name || avail[0]);
          }
        }

        if (configData) {
          setConfig(configData);
        }
      } catch (err) {
        console.error('Failed to load initial config/models', err);
      }
    }
    loadData();
  }, []);

  // Load sessions when user changes
  const loadSessions = async () => {
    try {
      const sessionList = await api.getSessions();
      setSessions(sessionList);
      if (sessionList.length > 0 && !currentSession) {
        setCurrentSession(sessionList[0]);
      }
    } catch (err) {
      console.error('Failed to load sessions', err);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [user]);

  const handleCreateSession = async () => {
    try {
      const now = new Date();
      const dateStr = now.toLocaleDateString('en-GB');
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const title = `${dateStr} | ${timeStr}`;

      const newSession = await api.createSession(title);
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSession(newSession);

      // Refresh config to update remaining daily limit
      api.getConfig().then(setConfig).catch(console.error);
    } catch (err) {
      alert(err.message || 'Failed to create session');
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await api.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        const remaining = sessions.filter((s) => s.id !== sessionId);
        setCurrentSession(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (err) {
      alert(err.message || 'Failed to delete session');
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-50 font-sans">
      <Navbar
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        models={models}
        onOpenAuth={() => setShowAuthModal(true)}
      />

      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar
          sessions={sessions}
          currentSession={currentSession}
          onSelectSession={setCurrentSession}
          onCreateSession={handleCreateSession}
          onDeleteSession={handleDeleteSession}
          remainingLimit={config?.remaining_limit ?? 15}
          dailyLimit={config?.daily_limit ?? 15}
          isSupabaseConnected={config?.is_supabase_connected ?? false}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        <main className="flex-1 flex flex-col overflow-hidden relative">
          {currentSession ? (
            <ChatView
              session={currentSession}
              selectedModel={selectedModel}
              onRefreshSessions={() => {
                loadSessions();
                api.getConfig().then(setConfig).catch(console.error);
              }}
            />
          ) : (
            <WelcomeView onCreateSession={handleCreateSession} />
          )}
        </main>
      </div>

      {showAuthModal && (
        <AuthModal onClose={() => setShowAuthModal(false)} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
