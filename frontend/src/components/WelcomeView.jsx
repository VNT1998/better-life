import React from 'react';
import {
  Activity,
  Plus,
  Shield,
  Zap,
  MessageSquare,
  FileText,
  Sparkles,
  Server,
} from 'lucide-react';

export default function WelcomeView({ onCreateSession, onSelectSample }) {
  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-12 flex flex-col items-center justify-center text-center">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Hero Icon */}
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-tr from-sky-500 to-blue-600 text-white shadow-xl shadow-sky-500/25 animate-in zoom-in-75 duration-300">
          <Activity className="w-10 h-10 animate-pulse" />
        </div>

        {/* Title */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold tracking-wide uppercase">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>AI-Powered Health Intelligence</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            BetterLife AI
          </h2>
          <p className="text-base text-slate-600 font-medium">
            Discover a Better, Healthier You with AI
          </p>
          <p className="text-sm text-slate-500 max-w-lg mx-auto">
            Upload your laboratory blood tests or use our comprehensive sample report. Get immediate AI-generated risk evaluations, lifestyle recommendations, and interactive clinical follow-up Q&A.
          </p>
        </div>

        {/* CTA Button */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={onCreateSession}
            className="w-full sm:w-auto px-7 py-3.5 bg-sky-500 hover:bg-sky-600 active:bg-sky-700 text-white rounded-2xl font-semibold text-sm shadow-lg shadow-sky-500/25 flex items-center justify-center gap-2 transition cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Create New Analysis Session</span>
          </button>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-8 text-left border-t border-slate-200/80">
          <div className="p-4 rounded-2xl bg-white border border-slate-200/70 shadow-xs">
            <div className="w-8 h-8 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center mb-2.5">
              <FileText className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
              Smart PDF Extraction
            </h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Extracts CBC, Lipid Panels, Liver & Kidney markers from your medical PDF with automated validation.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-white border border-slate-200/70 shadow-xs">
            <div className="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-2.5">
              <Server className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
              Self-Hosted Ollama
            </h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Zero external commercial API dependencies. Direct inference powered by your Ollama server with multi-model fallback.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-white border border-slate-200/70 shadow-xs">
            <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-2.5">
              <MessageSquare className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
              RAG Follow-up Q&A
            </h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Chat interactively with your report. Ask specific questions about lab values, reference ranges, and symptoms.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
