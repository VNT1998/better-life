import React, { useState } from 'react';
import {
  Plus,
  MessageSquare,
  Trash2,
  Check,
  X,
  Sparkles,
  Zap,
  ShieldCheck,
  Calendar,
} from 'lucide-react';

export default function Sidebar({
  sessions,
  currentSession,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  remainingLimit = 15,
  dailyLimit = 15,
  isSupabaseConnected = false,
  isOpen = true,
  onClose,
}) {
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);

  const handleDeleteClick = (e, sessionId) => {
    e.stopPropagation();
    setDeleteConfirmId(sessionId);
  };

  const handleConfirmDelete = (e, sessionId) => {
    e.stopPropagation();
    onDeleteSession(sessionId);
    setDeleteConfirmId(null);
  };

  const handleCancelDelete = (e) => {
    e.stopPropagation();
    setDeleteConfirmId(null);
  };

  return (
    <aside
      className={`fixed lg:static inset-y-0 left-0 z-40 w-72 bg-white border-r border-slate-200/80 flex flex-col transition-transform duration-200 ease-in-out ${
        isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}
    >
      {/* Top Action */}
      <div className="p-4 border-b border-slate-100">
        <button
          onClick={onCreateSession}
          className="w-full py-2.5 px-4 bg-sky-500 hover:bg-sky-600 active:bg-sky-700 text-white rounded-xl font-medium text-sm flex items-center justify-center gap-2 shadow-md shadow-sky-500/20 transition cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Analysis Session</span>
        </button>

        {/* Daily limit badge */}
        <div className="mt-3 p-3 bg-sky-50/70 border border-sky-100 rounded-xl text-center">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="flex items-center gap-1 font-medium">
              <Zap className="w-3 h-3 text-sky-500" /> Daily Limit
            </span>
            <span
              className={`font-semibold ${
                remainingLimit <= 3 ? 'text-rose-600' : 'text-sky-700'
              }`}
            >
              {remainingLimit}/{dailyLimit} left
            </span>
          </div>
          <div className="w-full h-1.5 bg-sky-200/50 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                remainingLimit <= 3 ? 'bg-rose-500' : 'bg-sky-500'
              }`}
              style={{
                width: `${Math.max(5, (remainingLimit / dailyLimit) * 100)}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="px-2 py-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Previous Sessions
        </div>

        {sessions && sessions.length > 0 ? (
          sessions.map((session) => {
            const isSelected = currentSession?.id === session.id;
            const isDeleting = deleteConfirmId === session.id;

            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session)}
                className={`group relative flex items-center justify-between p-2.5 rounded-xl text-sm transition cursor-pointer ${
                  isSelected
                    ? 'bg-sky-50 text-sky-900 font-medium border border-sky-200/80 shadow-xs'
                    : 'text-slate-700 hover:bg-slate-50 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 pr-2">
                  <MessageSquare
                    className={`w-4 h-4 shrink-0 ${
                      isSelected ? 'text-sky-600' : 'text-slate-400 group-hover:text-slate-600'
                    }`}
                  />
                  <div className="truncate text-xs font-medium">
                    {session.title || 'Analysis Session'}
                  </div>
                </div>

                {/* Actions */}
                <div className="shrink-0 flex items-center">
                  {isDeleting ? (
                    <div className="flex items-center gap-1 bg-white p-1 rounded-lg shadow-sm border border-slate-200">
                      <button
                        type="button"
                        onClick={(e) => handleConfirmDelete(e, session.id)}
                        className="p-1 hover:bg-rose-100 text-rose-600 rounded transition"
                        title="Confirm Delete"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={handleCancelDelete}
                        className="p-1 hover:bg-slate-100 text-slate-500 rounded transition"
                        title="Cancel"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={(e) => handleDeleteClick(e, session.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-rose-50 text-slate-400 hover:text-rose-600 rounded-lg transition"
                      title="Delete session"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="p-4 text-center text-xs text-slate-400">
            No previous sessions yet. Click "New Analysis Session" to begin!
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-100 text-[11px] text-slate-500 bg-slate-50/50 space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" /> Auth & DB
          </span>
          <span className="font-medium text-slate-700">
            {isSupabaseConnected ? 'Supabase' : 'Local Mode'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span>AI Engine</span>
          <span className="font-medium text-sky-600">Ollama API</span>
        </div>
      </div>
    </aside>
  );
}
