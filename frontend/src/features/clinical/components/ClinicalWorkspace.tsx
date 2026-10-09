import React, { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api/client'
import type {
  ClinicalPatient,
  ClinicalDocument,
  PatientTimelineResponse,
  AuditEvent,
  KnowledgeBaseListResponse,
} from '@/lib/api/types'
import {
  FileText,
  Activity,
  BookOpen,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle2,
  Upload,
  RefreshCw,
  Search,
  User,
  Info,
} from 'lucide-react'

interface DocumentPageData {
  page_number: number
  char_count: number
  text_content?: string
  text_preview?: string
}

interface ExtendedClinicalDocument extends ClinicalDocument {
  pages?: DocumentPageData[]
}

interface ExtendedClinicalAnalysisResult {
  execution_id: string
  model_name: string
  findings?: Array<{
    finding: string
    risk_level: string
    clinical_rationale: string
    citations?: Array<{
      guideline_name: string
      organization: string
      section: string
      page?: number
      similarity_score: number
      relevant_excerpt: string
    }>
  }>
  dietary_lifestyle_recommendations?: string[]
  recommended_follow_up_tests?: string[]
  disclaimer?: string
  safety_verdict?: {
    passed: boolean
    status: string
    violations: string[]
    checks: Record<string, boolean>
    notes: string
  }
}

interface RagQueryResponse {
  query: string
  evidence_chunks: Array<{
    id: string
    title: string
    organization: string
    section: string
    page?: number
    text: string
    recommendation_level?: string
  }>
  total_matches: number
}

interface ClinicalWorkspaceProps {
  selectedModel: string
}

export function ClinicalWorkspace({ selectedModel }: ClinicalWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<string>('dashboard')
  const [patients, setPatients] = useState<ClinicalPatient[]>([])
  const [selectedPatient, setSelectedPatient] = useState<ClinicalPatient | null>(null)
  const [documents, setDocuments] = useState<ExtendedClinicalDocument[]>([])
  const [selectedDoc, setSelectedDoc] = useState<ExtendedClinicalDocument | null>(null)
  const [timeline, setTimeline] = useState<PatientTimelineResponse | null>(null)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseListResponse[]>([])
  const [ragQuery, setRagQuery] = useState<string>('')
  const [ragResults, setRagResults] = useState<RagQueryResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [analyzing, setAnalyzing] = useState<boolean>(false)
  const [analysisResult, setAnalysisResult] = useState<ExtendedClinicalAnalysisResult | null>(null)
  const [uploadError, setUploadError] = useState<string>('')

  const loadTimeline = useCallback(async (patientId: string) => {
    try {
      const tl = await api.getClinicalPatientTimeline(patientId)
      setTimeline(tl)
    } catch (err) {
      console.error('Failed to load timeline', err)
    }
  }, [])

  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      const [pts, docs, kbs, evts] = await Promise.all([
        api.listClinicalPatients().catch(() => []),
        api.listClinicalDocuments().catch(() => []),
        api.listKnowledgeBases().catch(() => []),
        api.getAuditEvents().catch(() => []),
      ])
      setPatients(pts)
      if (pts.length > 0) {
        setSelectedPatient((prev) => {
          if (!prev) {
            loadTimeline(pts[0].id)
            return pts[0]
          }
          return prev
        })
      }
      setDocuments(docs as ExtendedClinicalDocument[])
      if (docs.length > 0) {
        setSelectedDoc((prev) => prev ?? (docs[0] as ExtendedClinicalDocument))
      }
      setKnowledgeBases(kbs)
      setAuditEvents(evts)
    } catch (err) {
      console.error('Failed to load clinical workspace data', err)
    } finally {
      setLoading(false)
    }
  }, [loadTimeline])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const handleCreatePatient = async (e: React.MouseEvent) => {
    e.preventDefault()
    const name = prompt('Enter Patient Full Name:')
    if (!name) return
    const age = parseInt(prompt('Enter Patient Age:', '45') || '45', 10)
    const gender = prompt('Enter Biological Sex (Male/Female):', 'Female') || 'Female'

    try {
      const newP = await api.createClinicalPatient({ name, age, gender })
      setPatients((prev) => [newP, ...prev])
      setSelectedPatient(newP)
      loadTimeline(newP.id)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      alert('Error creating patient: ' + msg)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadError('')
    setLoading(true)

    try {
      const doc = await api.uploadClinicalDocument(file)
      const extDoc = doc as ExtendedClinicalDocument
      setDocuments((prev) => [extDoc, ...prev])
      setSelectedDoc(extDoc)
      api.getAuditEvents().then(setAuditEvents).catch(console.error)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setUploadError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleRunAnalysis = async () => {
    if (!selectedPatient || !selectedDoc) {
      alert('Please select both a Patient and an Ingested Document.')
      return
    }
    setAnalyzing(true)
    setAnalysisResult(null)

    try {
      const res = await api.analyzeClinicalPatient(
        selectedPatient.id,
        selectedDoc.id,
        selectedModel
      )
      setAnalysisResult(res as unknown as ExtendedClinicalAnalysisResult)
      setActiveTab('analysis')
      loadTimeline(selectedPatient.id)
      api.getAuditEvents().then(setAuditEvents).catch(console.error)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      alert('Analysis error: ' + msg)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleRagSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ragQuery.trim()) return
    try {
      const res = await api.queryKnowledgeBase('clinical-standards-v1', ragQuery, 4)
      setRagResults(res as unknown as RagQueryResponse)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      alert('RAG search error: ' + msg)
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Workspace Sub-Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center font-bold text-sm shadow-sm">
            CEI
          </div>
          <div>
            <h1 className="text-base font-semibold text-slate-800 leading-tight">
              Clinical Evidence Intelligence Platform
            </h1>
            <p className="text-xs text-slate-500">
              Reference AI Workload • Longitudinal Modeling • Evidence-Grounded RAG • Deterministic
              Safety
            </p>
          </div>
        </div>

        {/* Action button */}
        <div className="flex items-center gap-2">
          <button
            onClick={loadAll}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleRunAnalysis}
            disabled={analyzing || !selectedPatient || !selectedDoc}
            className="flex items-center gap-2 px-3 py-1.5 bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white rounded-lg text-xs font-medium shadow-sm transition"
          >
            <Activity className="w-4 h-4" />
            {analyzing ? 'Analyzing Pipeline...' : 'Run Pipeline Analysis'}
          </button>
        </div>
      </div>

      {/* Tabs Bar */}
      <div className="bg-white border-b border-slate-200 px-6 flex gap-6 shrink-0">
        {[
          { id: 'dashboard', label: 'Dashboard & Patient', icon: User },
          { id: 'documents', label: 'Document Viewer & OCR', icon: FileText },
          { id: 'timeline', label: 'Longitudinal Timeline', icon: TrendingUp },
          { id: 'evidence', label: 'Evidence Explorer (RAG)', icon: BookOpen },
          { id: 'analysis', label: 'Analysis & Provenance Graph', icon: Activity },
          { id: 'audit', label: 'Audit Trail & Safety', icon: ShieldCheck },
        ].map((tab) => {
          const Icon = tab.icon
          const active = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-3 border-b-2 text-xs font-medium transition ${
                active
                  ? 'border-teal-600 text-teal-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* TAB 1: DASHBOARD & PATIENT */}
        {activeTab === 'dashboard' && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Patient Selection Card */}
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-800 text-sm flex items-center gap-2">
                    <User className="w-4 h-4 text-teal-600" />
                    Enrolled Patients ({patients.length})
                  </h3>
                  <button
                    onClick={handleCreatePatient}
                    className="text-xs text-teal-600 hover:underline font-medium"
                  >
                    + New Patient
                  </button>
                </div>
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {patients.map((p) => (
                    <div
                      key={p.id}
                      onClick={() => {
                        setSelectedPatient(p)
                        loadTimeline(p.id)
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          setSelectedPatient(p)
                          loadTimeline(p.id)
                        }
                      }}
                      role="button"
                      tabIndex={0}
                      className={`p-3 rounded-lg border text-xs cursor-pointer transition ${
                        selectedPatient?.id === p.id
                          ? 'border-teal-500 bg-teal-50/50 text-teal-900 font-medium'
                          : 'border-slate-100 hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      <div className="font-semibold">{p.name}</div>
                      <div className="text-slate-500 text-[11px]">
                        {p.age} y/o • {p.gender} • ID: {p.id.slice(0, 8)}...
                      </div>
                    </div>
                  ))}
                  {patients.length === 0 && (
                    <p className="text-xs text-slate-400 py-3 text-center">
                      No patients enrolled yet.
                    </p>
                  )}
                </div>
              </div>

              {/* Ingested Documents Card */}
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-800 text-sm flex items-center gap-2">
                    <FileText className="w-4 h-4 text-teal-600" />
                    Ingested Documents ({documents.length})
                  </h3>
                  <label className="text-xs text-teal-600 hover:underline font-medium cursor-pointer">
                    + Ingest PDF
                    <input
                      type="file"
                      onChange={handleFileUpload}
                      accept=".pdf,.txt,.png,.jpg"
                      className="hidden"
                    />
                  </label>
                </div>
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {documents.map((d) => (
                    <div
                      key={d.id}
                      onClick={() => setSelectedDoc(d)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') setSelectedDoc(d)
                      }}
                      role="button"
                      tabIndex={0}
                      className={`p-3 rounded-lg border text-xs cursor-pointer transition ${
                        selectedDoc?.id === d.id
                          ? 'border-teal-500 bg-teal-50/50 text-teal-900 font-medium'
                          : 'border-slate-100 hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      <div className="font-semibold truncate">{d.filename}</div>
                      <div className="text-slate-500 text-[11px]">
                        {d.page_count} page(s) • {d.file_type.toUpperCase()}
                      </div>
                    </div>
                  ))}
                  {documents.length === 0 && (
                    <p className="text-xs text-slate-400 py-3 text-center">
                      No documents ingested.
                    </p>
                  )}
                </div>
              </div>

              {/* Execution Pipeline Status */}
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <h3 className="font-semibold text-slate-800 text-sm mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-teal-600" />
                  Workload Status
                </h3>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between py-1.5 border-b border-slate-100">
                    <span className="text-slate-500">Target Framework:</span>
                    <span className="font-semibold text-slate-800">Nuvorix AI Reference</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-100">
                    <span className="text-slate-500">Selected Patient:</span>
                    <span className="font-medium text-teal-700 truncate max-w-[150px]">
                      {selectedPatient?.name || 'None'}
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-100">
                    <span className="text-slate-500">Selected Document:</span>
                    <span className="font-medium text-teal-700 truncate max-w-[150px]">
                      {selectedDoc?.filename || 'None'}
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-500">Safety Gating:</span>
                    <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Deterministic Active
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Run Banner */}
            <div className="bg-gradient-to-r from-teal-700 to-slate-800 rounded-xl p-6 text-white shadow-sm flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold">
                  Ready to run full Evidence Intelligence Pipeline?
                </h2>
                <p className="text-xs text-teal-100 mt-1 max-w-xl">
                  Executes PDF page segmentation, Pydantic structured extraction, longitudinal delta
                  calculation, guideline vector RAG, and deterministic safety checks with an audit
                  trail.
                </p>
              </div>
              <button
                onClick={handleRunAnalysis}
                disabled={analyzing || !selectedPatient || !selectedDoc}
                className="px-5 py-2.5 bg-white text-teal-900 hover:bg-teal-50 disabled:bg-slate-300 font-semibold rounded-lg text-xs shadow-md transition shrink-0"
              >
                {analyzing ? 'Processing...' : 'Run Pipeline Now →'}
              </button>
            </div>
          </div>
        )}

        {/* TAB 2: DOCUMENT VIEWER & SEGMENTATION */}
        {activeTab === 'documents' && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
                <div>
                  <h2 className="text-sm font-bold text-slate-800">
                    Document Segmentation & Source Provenance Viewer
                  </h2>
                  <p className="text-xs text-slate-500">
                    Inspect extracted document pages, character counts, and raw text representations
                  </p>
                </div>
                <label className="flex items-center gap-2 px-3 py-1.5 bg-teal-600 text-white rounded-lg text-xs font-medium cursor-pointer hover:bg-teal-700 transition">
                  <Upload className="w-3.5 h-3.5" />
                  Upload Document
                  <input
                    type="file"
                    onChange={handleFileUpload}
                    accept=".pdf,.txt,.png,.jpg"
                    className="hidden"
                  />
                </label>
              </div>

              {uploadError && (
                <div className="p-3 mb-4 rounded-lg bg-red-50 text-red-700 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  {uploadError}
                </div>
              )}

              {selectedDoc ? (
                <div className="space-y-4">
                  <div className="bg-slate-50 p-4 rounded-lg flex items-center justify-between text-xs">
                    <div>
                      <span className="font-semibold text-slate-700">{selectedDoc.filename}</span>
                      <span className="text-slate-400 ml-2">({selectedDoc.page_count} pages)</span>
                    </div>
                    <span className="text-slate-400">ID: {selectedDoc.id}</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedDoc.pages?.map((page) => (
                      <div
                        key={page.page_number}
                        className="border border-slate-200 rounded-lg p-4 bg-white shadow-xs space-y-2"
                      >
                        <div className="flex justify-between items-center text-xs font-semibold text-slate-700 pb-2 border-b border-slate-100">
                          <span>Page {page.page_number}</span>
                          <span className="text-slate-400 text-[11px]">
                            {page.char_count} chars
                          </span>
                        </div>
                        <pre className="text-xs font-mono text-slate-600 whitespace-pre-wrap max-h-60 overflow-y-auto bg-slate-50 p-3 rounded">
                          {page.text_content || page.text_preview}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400 text-xs">
                  No document selected. Upload or select a document to inspect segmentation.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: LONGITUDINAL TIMELINE */}
        {activeTab === 'timeline' && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
                <div>
                  <h2 className="text-sm font-bold text-slate-800">
                    Patient Longitudinal Timeline
                  </h2>
                  <p className="text-xs text-slate-500">
                    Biomarker trajectories over time (rising, falling, stable, new) with computed
                    percentage shifts
                  </p>
                </div>
                <div className="text-xs text-slate-600 font-medium">
                  Patient:{' '}
                  <span className="text-teal-700 font-semibold">
                    {selectedPatient?.name || 'None'}
                  </span>
                </div>
              </div>

              {timeline && timeline.timelines?.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {timeline.timelines.map((item) => {
                    const isRising = item.trend === 'rising'
                    const isFalling = item.trend === 'falling'
                    const isStable = item.trend === 'stable'

                    return (
                      <div
                        key={item.biomarker}
                        className="border border-slate-200 rounded-xl p-4 bg-white shadow-xs space-y-3"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-800">{item.biomarker}</span>
                          <span
                            className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                              isRising
                                ? 'bg-amber-100 text-amber-800'
                                : isFalling
                                  ? 'bg-blue-100 text-blue-800'
                                  : 'bg-emerald-100 text-emerald-800'
                            }`}
                          >
                            {isRising && <TrendingUp className="w-3 h-3" />}
                            {isFalling && <TrendingDown className="w-3 h-3" />}
                            {isStable && <Minus className="w-3 h-3" />}
                            {item.trend.toUpperCase()}
                          </span>
                        </div>

                        <div className="space-y-1.5 text-xs">
                          {item.data_points.map((pt, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between py-1 border-b border-slate-50 text-slate-600"
                            >
                              <span className="text-slate-400 text-[11px]">{pt.date}</span>
                              <span className="font-semibold text-slate-800">
                                {pt.value_raw || pt.numeric_value} {pt.unit}
                              </span>
                              <span
                                className={`text-[10px] px-1.5 py-0.5 rounded ${
                                  pt.flag === 'NORMAL'
                                    ? 'bg-slate-100 text-slate-600'
                                    : 'bg-red-100 text-red-700 font-bold'
                                }`}
                              >
                                {pt.flag}
                              </span>
                            </div>
                          ))}
                        </div>

                        {item.clinical_interpretation && (
                          <div className="text-[11px] text-slate-500 bg-slate-50 p-2 rounded">
                            {item.clinical_interpretation}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400 text-xs">
                  No longitudinal data recorded for this patient yet. Run an analysis on a report to
                  begin tracking.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: EVIDENCE EXPLORER (RAG) */}
        {activeTab === 'evidence' && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="pb-4 border-b border-slate-100 mb-6">
                <h2 className="text-sm font-bold text-slate-800">
                  Clinical Guideline Knowledge Base & RAG Search
                </h2>
                <p className="text-xs text-slate-500 mb-3">
                  Authoritative clinical standards from ADA, AHA/ACC, KDIGO, WHO, and ASH
                </p>
                {knowledgeBases.length > 0 && (
                  <div className="flex gap-2 flex-wrap">
                    {knowledgeBases.map((kb) => (
                      <span
                        key={kb.knowledge_base_id}
                        className="text-[11px] bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full border border-slate-200 flex items-center gap-1.5"
                      >
                        <BookOpen className="w-3 h-3 text-teal-600" />
                        {kb.name} ({kb.total_guidelines} guidelines)
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Search Bar */}
              <form onSubmit={handleRagSearch} className="flex gap-2 mb-6">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    value={ragQuery}
                    onChange={(e) => setRagQuery(e.target.value)}
                    placeholder="Search clinical guidelines (e.g. 'Fasting blood sugar cutoffs', 'LDL target', 'Anemia hemoglobin threshold')..."
                    className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 text-white rounded-lg text-xs font-semibold hover:bg-teal-700 transition"
                >
                  Retrieve Evidence
                </button>
              </form>

              {/* RAG Results */}
              {ragResults ? (
                <div className="space-y-4">
                  <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                    Retrieved Guideline Chunks ({ragResults.evidence_chunks.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {ragResults.evidence_chunks.map((c) => (
                      <div
                        key={c.id}
                        className="border border-teal-200 bg-teal-50/20 rounded-xl p-4 space-y-2"
                      >
                        <div className="flex justify-between items-start">
                          <span className="font-bold text-xs text-teal-900">{c.title}</span>
                          <span className="text-[10px] bg-teal-100 text-teal-800 px-2 py-0.5 rounded font-semibold">
                            {c.recommendation_level || 'Guideline'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {c.organization} • Section: {c.section} (Page {c.page})
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed bg-white p-3 rounded border border-slate-100">
                          {c.text}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-500 py-6 text-center">
                  Search guidelines above to retrieve vector chunks and recommendation grades.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 5: ANALYSIS RESULT & VISUAL GRAPH */}
        {activeTab === 'analysis' && (
          <div className="max-w-6xl mx-auto space-y-6">
            {analysisResult ? (
              <div className="space-y-6">
                {/* Header Summary Card */}
                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                  <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                    <div>
                      <h2 className="text-base font-bold text-slate-800">
                        Evidence-Grounded Intelligence Report
                      </h2>
                      <p className="text-xs text-slate-500">
                        Execution ID:{' '}
                        <span className="font-mono text-teal-700">
                          {analysisResult.execution_id}
                        </span>{' '}
                        • Model:{' '}
                        <span className="font-semibold text-slate-700">
                          {analysisResult.model_name}
                        </span>
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs px-2.5 py-1 rounded-full font-bold flex items-center gap-1.5 ${
                          analysisResult.safety_verdict?.passed
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {analysisResult.safety_verdict?.passed ? (
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        ) : (
                          <AlertTriangle className="w-3.5 h-3.5" />
                        )}
                        {analysisResult.safety_verdict?.status}
                      </span>
                    </div>
                  </div>

                  {/* Core Visual Flow */}
                  <div className="my-6 p-4 rounded-xl bg-slate-50 border border-slate-200">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-3">
                      Provenance & Evidence Flow
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-2 text-center text-xs font-medium">
                      <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                        <span className="text-[10px] text-slate-400 block uppercase">
                          1. Clinical Finding
                        </span>
                        <span className="font-bold text-slate-800">
                          {analysisResult.findings?.length || 0} Key Biomarkers
                        </span>
                      </div>
                      <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                        <span className="text-[10px] text-slate-400 block uppercase">
                          2. Evidence Grounding
                        </span>
                        <span className="font-bold text-teal-700">ADA, ACC/AHA, KDIGO</span>
                      </div>
                      <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                        <span className="text-[10px] text-slate-400 block uppercase">
                          3. Source Provenance
                        </span>
                        <span className="font-bold text-slate-800">Page & Text Spans</span>
                      </div>
                      <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                        <span className="text-[10px] text-slate-400 block uppercase">
                          4. Safety Boundary
                        </span>
                        <span className="font-bold text-emerald-700">Deterministic Verified</span>
                      </div>
                    </div>
                  </div>

                  {/* Evidence Findings with Citations */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-bold text-slate-800">
                      Grounded Findings & Citations
                    </h3>
                    {analysisResult.findings?.map((f, i) => (
                      <div
                        key={i}
                        className="border border-slate-200 rounded-xl p-5 bg-white space-y-3"
                      >
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-slate-900">{f.finding}</h4>
                          <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-semibold">
                            Risk: {f.risk_level}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600">{f.clinical_rationale}</p>

                        {/* Citations Box */}
                        {f.citations && f.citations.length > 0 && (
                          <div className="bg-teal-50/50 border border-teal-100 rounded-lg p-3 space-y-2">
                            <span className="text-[11px] font-bold text-teal-900 block">
                              Authoritative Guideline Citations ({f.citations.length})
                            </span>
                            {f.citations.map((c, ci) => (
                              <div
                                key={ci}
                                className="text-xs text-slate-700 border-l-2 border-teal-500 pl-3 py-1 space-y-1"
                              >
                                <div className="font-semibold text-teal-950">
                                  {c.guideline_name} ({c.organization})
                                </div>
                                <div className="text-[11px] text-slate-500">
                                  Section: {c.section} {c.page ? `• Page ${c.page}` : ''} • Match:{' '}
                                  {(c.similarity_score * 100).toFixed(0)}%
                                </div>
                                <p className="italic text-[11px] text-slate-600 bg-white p-2 rounded border border-slate-100">
                                  "{c.relevant_excerpt}"
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Recommendations */}
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                      <h4 className="text-xs font-bold text-slate-800 mb-2">
                        Evidence-Based Lifestyle Guidance
                      </h4>
                      <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4">
                        {analysisResult.dietary_lifestyle_recommendations?.map((r, ri) => (
                          <li key={ri}>{r}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                      <h4 className="text-xs font-bold text-slate-800 mb-2">
                        Recommended Follow-Up Laboratory Tests
                      </h4>
                      <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4">
                        {analysisResult.recommended_follow_up_tests?.map((t, ti) => (
                          <li key={ti}>{t}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Disclaimer */}
                  {analysisResult.disclaimer && (
                    <div className="mt-6 p-3 rounded-lg bg-amber-50 text-amber-800 text-[11px] flex items-center gap-2">
                      <Info className="w-4 h-4 shrink-0" />
                      {analysisResult.disclaimer}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400 text-xs">
                No pipeline analysis generated yet. Click "Run Pipeline Analysis" in the top bar to
                run on the selected document.
              </div>
            )}
          </div>
        )}

        {/* TAB 6: AUDIT TRAIL & SAFETY GOVERNANCE */}
        {activeTab === 'audit' && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="pb-4 border-b border-slate-100 mb-6 flex justify-between items-center">
                <div>
                  <h2 className="text-sm font-bold text-slate-800">
                    Audit Trail & Safety Governance Log
                  </h2>
                  <p className="text-xs text-slate-500">
                    Immutable event log of data ingestion, model executions, and deterministic
                    safety checks
                  </p>
                </div>
                <span className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full font-mono font-semibold">
                  {auditEvents.length} Events Logged
                </span>
              </div>

              <div className="space-y-3">
                {auditEvents.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-4 rounded-lg border border-slate-100 bg-slate-50/50 flex items-start justify-between text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-800">{ev.event_type}</span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                            ev.status === 'SUCCESS'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {ev.status}
                        </span>
                      </div>
                      <div className="text-slate-500 text-[11px]">
                        Timestamp: {new Date(ev.timestamp).toLocaleString()} • ID:{' '}
                        {ev.id.slice(0, 8)}...
                      </div>
                      <pre className="text-[10px] font-mono text-slate-600 bg-white p-2 rounded border border-slate-100 mt-2">
                        {JSON.stringify(ev.payload, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))}

                {auditEvents.length === 0 && (
                  <div className="text-center py-12 text-slate-400 text-xs">
                    No audit events recorded yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ClinicalWorkspace
