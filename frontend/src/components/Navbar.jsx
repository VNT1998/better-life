import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Activity, LogOut, LogIn, Server } from 'lucide-react';

export default function Navbar({
  selectedModel,
  onSelectModel,
  models,
  onOpenAuth,
  mode,
  onToggleMode,
}) {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-200/80 px-4 lg:px-8 py-3 flex items-center justify-between">
      {/* Brand & Mode Switcher */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center text-white shadow-md shadow-sky-500/20">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900">
                BetterLife
              </h1>
              <span className="text-[10px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                Health AI
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              Discover a Better, Healthier You with AI
            </p>
          </div>
        </div>

        {/* Workspace Mode Switcher */}
        <div className="hidden sm:flex items-center bg-slate-100 p-1 rounded-xl text-xs font-semibold ml-2">
          <button
            onClick={() => onToggleMode('chat')}
            className={`px-3 py-1.5 rounded-lg transition ${
              mode === 'chat'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            💬 Health Chat
          </button>
          <button
            onClick={() => onToggleMode('clinical')}
            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
              mode === 'clinical'
                ? 'bg-teal-600 text-white shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            🔬 Clinical Intelligence
          </button>
        </div>
      </div>

      {/* Center / Model Selector */}
      <div className="hidden md:flex items-center gap-2">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-100/80 border border-slate-200/60 text-xs text-slate-700">
          <Server className="w-3.5 h-3.5 text-emerald-500" />
          <span className="font-medium text-slate-500">Ollama:</span>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            className="bg-transparent font-semibold text-slate-800 focus:outline-none cursor-pointer pr-1"
          >
            {models && models.length > 0 ? (
              models.map((m) => (
                <option key={m.name || m} value={m.name || m}>
                  {m.name || m}
                </option>
              ))
            ) : (
              <>
                <option value="gemma4:e4b">gemma4:e4b</option>
                <option value="phi4-mini:latest">phi4-mini:latest</option>
                <option value="granite4.1:3b">granite4.1:3b</option>
                <option value="qwen3.5:4b-mlx">qwen3.5:4b-mlx</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* User / Auth Section */}
      <div className="flex items-center gap-3">
        {isAuthenticated ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-right">
              <div className="hidden sm:block">
                <span className="text-xs text-slate-400 block leading-none">Welcome</span>
                <span className="text-sm font-semibold text-slate-800">
                  {user?.name || user?.email?.split('@')[0]}
                </span>
              </div>
              <div className="w-8 h-8 rounded-full bg-sky-100 border border-sky-300 text-sky-700 flex items-center justify-center font-bold text-xs uppercase">
                {(user?.name || user?.email || 'U')[0]}
              </div>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-600 text-white text-xs font-semibold shadow-sm transition cursor-pointer"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
}
