import { useState, useEffect, useCallback } from 'react'
import { AppProviders } from './providers'
import { useAuth } from '@/features/auth/context/AuthContext'
import { api } from '@/lib/api/client'
import { Navbar } from '@/components/Navbar'
import { Sidebar } from '@/features/sessions/components/Sidebar'
import { WelcomeView } from '@/features/sessions/components/WelcomeView'
import { ChatView } from '@/features/chat/components/ChatView'
import { AuthModal } from '@/features/auth/components/AuthModal'
import { ClinicalWorkspace } from '@/features/clinical/components/ClinicalWorkspace'
import type { Session, ModelOption } from '@/lib/api/types'

function MainApp() {
  const { user } = useAuth()
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSession, setCurrentSession] = useState<Session | null>(null)
  const [models, setModels] = useState<Array<ModelOption | string>>([])
  const [selectedModel, setSelectedModel] = useState<string>('gemma4:e4b')
  const [config, setConfig] = useState<Record<string, unknown> | null>(null)
  const [showAuthModal, setShowAuthModal] = useState<boolean>(false)
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true)
  const [appMode, setAppMode] = useState<'clinical' | 'chat'>('clinical')

  // Load configuration and models
  useEffect(() => {
    async function loadData() {
      try {
        const [modelsData, configData] = await Promise.all([
          api.getModels().catch(() => null),
          api.getConfig().catch(() => null),
        ])

        if (modelsData) {
          const avail = modelsData.available || []
          setModels(avail)
          if (modelsData.primary) {
            setSelectedModel(modelsData.primary)
          } else if (avail.length > 0) {
            setSelectedModel(avail[0].name || avail[0].model)
          }
        }

        if (configData) {
          setConfig(configData)
        }
      } catch (err) {
        console.error('Failed to load initial config/models', err)
      }
    }
    loadData()
  }, [])

  // Load sessions when user changes
  const loadSessions = useCallback(async () => {
    try {
      const sessionList = await api.getSessions()
      setSessions(sessionList)
      if (sessionList.length > 0 && !currentSession) {
        setCurrentSession(sessionList[0])
      }
    } catch (err) {
      console.error('Failed to load sessions', err)
    }
  }, [currentSession])

  useEffect(() => {
    loadSessions()
  }, [user, loadSessions])

  const handleCreateSession = async () => {
    try {
      const now = new Date()
      const dateStr = now.toLocaleDateString('en-GB')
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      const title = `${dateStr} | ${timeStr}`

      const newSession = await api.createSession(title)
      setSessions((prev) => [newSession, ...prev])
      setCurrentSession(newSession)

      // Refresh config to update remaining daily limit
      api.getConfig().then(setConfig).catch(console.error)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create session'
      alert(msg)
    }
  }

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await api.deleteSession(sessionId)
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
      if (currentSession?.id === sessionId) {
        const remaining = sessions.filter((s) => s.id !== sessionId)
        setCurrentSession(remaining.length > 0 ? remaining[0] : null)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete session'
      alert(msg)
    }
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-50 font-sans">
      <Navbar
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        models={models}
        onOpenAuth={() => setShowAuthModal(true)}
        mode={appMode}
        onToggleMode={setAppMode}
      />

      {appMode === 'clinical' ? (
        <ClinicalWorkspace selectedModel={selectedModel} />
      ) : (
        <div className="flex flex-1 overflow-hidden relative">
          <Sidebar
            sessions={sessions}
            currentSession={currentSession}
            onSelectSession={setCurrentSession}
            onCreateSession={handleCreateSession}
            onDeleteSession={handleDeleteSession}
            remainingLimit={
              typeof config?.remaining_limit === 'number' ? config.remaining_limit : 15
            }
            dailyLimit={typeof config?.daily_limit === 'number' ? config.daily_limit : 15}
            isSupabaseConnected={Boolean(config?.is_supabase_connected)}
            supabaseStatus={
              typeof config?.supabase_status === 'string' ? config.supabase_status : null
            }
            isOpen={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
          />

          <main className="flex-1 flex flex-col overflow-hidden relative">
            {currentSession ? (
              <ChatView
                session={currentSession}
                selectedModel={selectedModel}
                onRefreshSessions={() => {
                  loadSessions()
                  api.getConfig().then(setConfig).catch(console.error)
                }}
              />
            ) : (
              <WelcomeView onCreateSession={handleCreateSession} />
            )}
          </main>
        </div>
      )}

      {showAuthModal && <AuthModal onClose={() => setShowAuthModal(false)} />}
    </div>
  )
}

export function App() {
  return (
    <AppProviders>
      <MainApp />
    </AppProviders>
  )
}

export default App
