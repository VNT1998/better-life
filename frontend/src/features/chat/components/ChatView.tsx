import React, { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { api } from '@/lib/api/client'
import { AnalysisForm } from '@/features/clinical/components/AnalysisForm'
import type { Session, ChatMessage } from '@/lib/api/types'
import {
  Send,
  User,
  Bot,
  Sparkles,
  AlertCircle,
  FileSpreadsheet,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

interface ChatViewProps {
  session: Session
  selectedModel: string
  onRefreshSessions?: () => void
}

export function ChatView({ session, selectedModel, onRefreshSessions }: ChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [query, setQuery] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [showAnalysisForm, setShowAnalysisForm] = useState<boolean>(false)
  const [error, setError] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const fetchMessages = useCallback(async () => {
    if (!session?.id) return
    try {
      const msgs = await api.getSessionMessages(session.id)
      setMessages(msgs)
      // If there are no messages, show the analysis form by default
      if (!msgs || msgs.length === 0) {
        setShowAnalysisForm(true)
      }
    } catch (err) {
      console.error('Failed to load messages', err)
    }
  }, [session?.id])

  useEffect(() => {
    fetchMessages()
  }, [fetchMessages])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleAnalysisSuccess = () => {
    setShowAnalysisForm(false)
    fetchMessages()
    if (onRefreshSessions) onRefreshSessions()
  }

  const handleSendQuestion = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!query.trim() || loading) return

    const userQuestion = query.trim()
    setQuery('')
    setError('')

    // 1. Optimistically append user message to UI
    const tempUserMsg: ChatMessage = {
      id: `temp_${Date.now()}`,
      role: 'user',
      content: userQuestion,
      created_at: new Date().toISOString(),
    }

    // 2. Prepare streaming assistant placeholder
    const tempAssistantId = `res_${Date.now()}`
    const tempAssistantMsg: ChatMessage = {
      id: tempAssistantId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, tempUserMsg, tempAssistantMsg])
    setLoading(true)

    try {
      let accumulatedContent = ''
      await api.streamChatMessage(
        {
          sessionId: session.id,
          query: userQuestion,
          model: selectedModel,
        },
        (token: string, _done: boolean) => {
          if (token) {
            accumulatedContent += token
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAssistantId ? { ...msg, content: accumulatedContent } : msg
              )
            )
          }
        }
      )
    } catch {
      // Fallback to standard non-streaming API if SSE is unavailable
      try {
        const res = await api.sendChatMessage({
          sessionId: session.id,
          query: userQuestion,
          model: selectedModel,
        })
        setMessages((prev) =>
          prev.map((msg) => (msg.id === tempAssistantId ? { ...msg, content: res.content } : msg))
        )
      } catch (fallbackErr: unknown) {
        const msg =
          fallbackErr instanceof Error ? fallbackErr.message : 'Failed to get answer from Ollama'
        setError(msg)
        // Remove empty assistant message on total failure
        setMessages((prev) => prev.filter((m) => m.id !== tempAssistantId))
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
  }

  const suggestions = [
    'Explain my Hemoglobin and RBC counts in simple terms',
    'Are my cholesterol and lipid levels high or normal?',
    'What dietary and lifestyle changes should I prioritize?',
    'What follow-up tests are recommended?',
  ]

  // Filter out internal system metadata messages
  const visibleMessages = messages.filter((m) => m.role !== 'system')

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50/50 overflow-hidden">
      {/* Session Header */}
      <div className="bg-white border-b border-slate-200/80 px-6 py-4 flex items-center justify-between shadow-xs">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>📊</span>
            <span>{session.title || 'Analysis Session'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Diagnostic insights & follow-up consultation with Ollama
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowAnalysisForm(!showAnalysisForm)}
          className="text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 hover:border-sky-300 hover:bg-sky-50 text-slate-700 flex items-center gap-1.5 transition cursor-pointer"
        >
          <FileSpreadsheet className="w-3.5 h-3.5 text-sky-500" />
          <span>{showAnalysisForm ? 'Hide Form' : 'New / Update Report'}</span>
          {showAnalysisForm ? (
            <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          )}
        </button>
      </div>

      {/* Main Chat Content */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {/* Collapsible Analysis Form */}
        {showAnalysisForm && (
          <AnalysisForm
            sessionId={session.id}
            selectedModel={selectedModel}
            onAnalysisSuccess={handleAnalysisSuccess}
          />
        )}

        {visibleMessages.length === 0 && !showAnalysisForm && (
          <div className="text-center py-12 px-4">
            <div className="w-14 h-14 bg-sky-100 text-sky-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FileSpreadsheet className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-slate-800">
              No analysis found for this session
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              Upload a blood report PDF or use our sample report to generate your health analysis.
            </p>
            <button
              onClick={() => setShowAnalysisForm(true)}
              className="px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-xl text-xs font-semibold shadow-sm transition"
            >
              Open Analysis Form
            </button>
          </div>
        )}

        {/* Message stream */}
        {visibleMessages.map((msg, idx) => {
          const isUser = msg.role === 'user'

          return (
            <div
              key={msg.id || idx}
              className={`flex gap-3.5 max-w-4xl mx-auto ${
                isUser ? 'justify-end' : 'justify-start'
              }`}
            >
              {!isUser && (
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm shadow-sky-500/20">
                  <Bot className="w-5 h-5" />
                </div>
              )}

              <div
                className={`rounded-2xl p-4 sm:p-5 text-sm transition shadow-xs ${
                  isUser
                    ? 'bg-sky-500 text-white font-medium max-w-xl rounded-tr-xs'
                    : 'bg-white border border-slate-200/80 text-slate-800 max-w-3xl rounded-tl-xs'
                }`}
              >
                {isUser ? (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div className="prose prose-sm max-w-none text-slate-800 prose-headings:text-slate-900 prose-headings:font-bold prose-p:leading-relaxed prose-li:my-0.5 prose-blockquote:border-l-sky-500 prose-blockquote:bg-sky-50/50 prose-blockquote:py-1 prose-blockquote:px-3 prose-blockquote:rounded-r-lg prose-blockquote:text-slate-700">
                    <ReactMarkdown>{msg.content || '...'}</ReactMarkdown>
                  </div>
                )}
              </div>

              {isUser && (
                <div className="w-9 h-9 rounded-xl bg-slate-200 text-slate-600 flex items-center justify-center shrink-0 font-bold text-xs uppercase">
                  <User className="w-5 h-5" />
                </div>
              )}
            </div>
          )
        })}

        {/* Loading indicator */}
        {loading && (
          <div className="flex gap-3.5 max-w-4xl mx-auto justify-start items-center">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm shadow-sky-500/20">
              <Bot className="w-5 h-5 animate-pulse" />
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 text-xs text-slate-500 flex items-center gap-2.5 shadow-xs">
              <div className="w-3.5 h-3.5 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
              <span>Analyzing report with Ollama...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="max-w-4xl mx-auto p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Follow-up suggestions & Input Bar */}
      {visibleMessages.length > 0 && (
        <div className="bg-white border-t border-slate-200/80 p-4">
          {/* Suggestion Chips */}
          <div className="max-w-4xl mx-auto mb-3 flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <span className="text-slate-400 font-medium shrink-0 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-sky-500" /> Suggestions:
            </span>
            {suggestions.map((s, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleSuggestionClick(s)}
                className="shrink-0 px-3 py-1 rounded-full bg-slate-100 hover:bg-sky-50 hover:text-sky-700 text-slate-600 border border-slate-200/70 transition cursor-pointer"
              >
                {s}
              </button>
            ))}
          </div>

          {/* Input form */}
          <form onSubmit={handleSendQuestion} className="max-w-4xl mx-auto flex items-center gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a follow-up question about the report..."
                disabled={loading}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="p-3 bg-sky-500 hover:bg-sky-600 active:bg-sky-700 text-white rounded-xl shadow-md shadow-sky-500/20 transition cursor-pointer disabled:opacity-40"
              title="Send question"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

export default ChatView
