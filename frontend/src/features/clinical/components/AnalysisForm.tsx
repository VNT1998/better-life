import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api/client'
import {
  Upload,
  FileText,
  CheckCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  HeartPulse,
} from 'lucide-react'

interface AnalysisFormProps {
  sessionId: string
  selectedModel: string
  onAnalysisSuccess?: (res: { success: boolean; analysis: string; session_id: string }) => void
  isCollapsed?: boolean
}

export function AnalysisForm({ sessionId, selectedModel, onAnalysisSuccess }: AnalysisFormProps) {
  const [reportSource, setReportSource] = useState<'upload' | 'sample'>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [reportText, setReportText] = useState<string>('')
  const [sampleText, setSampleText] = useState<string>('')
  const [patientName, setPatientName] = useState<string>('')
  const [age, setAge] = useState<string>('35')
  const [gender, setGender] = useState<string>('Male')
  const [showPreview, setShowPreview] = useState<boolean>(false)
  const [loading, setLoading] = useState<boolean>(false)
  const [extracting, setExtracting] = useState<boolean>(false)
  const [error, setError] = useState<string>('')

  // Load sample report on mount
  useEffect(() => {
    api
      .getSampleReport()
      .then((text) => {
        setSampleText(text)
        if (reportSource === 'sample') {
          setReportText(text)
        }
      })
      .catch(console.error)
  }, [reportSource])

  const handleSourceChange = (source: 'upload' | 'sample') => {
    setReportSource(source)
    setError('')
    if (source === 'sample') {
      setReportText(sampleText)
    } else {
      setReportText('')
      setFile(null)
    }
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return

    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Please upload a valid PDF file.')
      return
    }

    if (selectedFile.size > 20 * 1024 * 1024) {
      setError('File size exceeds the 20MB limit.')
      return
    }

    setFile(selectedFile)
    setError('')
    setExtracting(true)

    try {
      const extracted = await api.extractPdf(selectedFile)
      setReportText(extracted)
      setShowPreview(true)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to extract text from PDF'
      setError(msg)
      setFile(null)
      setReportText('')
    } finally {
      setExtracting(false)
    }
  }

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!patientName.trim()) {
      setError('Please enter patient name')
      return
    }
    const parsedAge = parseInt(age, 10)
    if (!age || isNaN(parsedAge) || parsedAge <= 0) {
      setError('Please enter a valid age')
      return
    }
    if (!reportText.trim()) {
      setError('Please upload a PDF or choose the Sample PDF before analyzing')
      return
    }

    setLoading(true)
    try {
      const res = await api.runAnalysis({
        sessionId,
        patientName: patientName.trim(),
        age: parsedAge,
        gender,
        reportText,
        model: selectedModel,
      })

      if (onAnalysisSuccess) {
        onAnalysisSuccess(res)
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Analysis failed. Please check Ollama server status.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden mb-6">
      {/* Source Toggle */}
      <div className="p-5 border-b border-slate-100 bg-slate-50/50">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
          1. Choose Report Source
        </label>
        <div className="grid grid-cols-2 gap-3 max-w-md">
          <button
            type="button"
            onClick={() => handleSourceChange('upload')}
            className={`py-3 px-4 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 border transition cursor-pointer ${
              reportSource === 'upload'
                ? 'bg-sky-50 border-sky-400 text-sky-800 shadow-xs'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Upload className="w-4 h-4 text-sky-500" />
            <span>Upload PDF</span>
          </button>

          <button
            type="button"
            onClick={() => handleSourceChange('sample')}
            className={`py-3 px-4 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 border transition cursor-pointer ${
              reportSource === 'sample'
                ? 'bg-sky-50 border-sky-400 text-sky-800 shadow-xs'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            <FileText className="w-4 h-4 text-sky-500" />
            <span>Use Sample PDF</span>
          </button>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Upload Dropzone or Sample indicator */}
        {reportSource === 'upload' ? (
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-2">
              Blood Report PDF (Max 20MB)
            </label>
            <div className="relative border-2 border-dashed border-slate-200 hover:border-sky-400 rounded-2xl p-6 text-center transition bg-slate-50/40 hover:bg-sky-50/20">
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                disabled={extracting}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center justify-center">
                <div className="w-12 h-12 rounded-full bg-sky-100 flex items-center justify-center text-sky-600 mb-2">
                  <Upload className="w-6 h-6" />
                </div>
                <span className="text-sm font-semibold text-slate-700">
                  {file ? file.name : 'Click or drag PDF here to upload'}
                </span>
                <span className="text-xs text-slate-400 mt-1">
                  Only medical reports in PDF format (up to 50 pages)
                </span>
              </div>
            </div>
            {extracting && (
              <div className="mt-2 text-xs text-sky-600 font-medium flex items-center gap-2">
                <div className="w-3.5 h-3.5 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
                <span>Extracting and verifying medical text...</span>
              </div>
            )}
          </div>
        ) : (
          <div className="p-4 bg-sky-50/60 border border-sky-200/80 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-sky-500 text-white flex items-center justify-center shadow-xs">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-900">
                  Standard Comprehensive Blood Test Report
                </h4>
                <p className="text-xs text-slate-500">
                  Includes CBC, Lipid Profile, Liver Panel, Kidney Markers, HbA1c
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Extracted Text Accordion Preview */}
        {reportText && (
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <button
              type="button"
              onClick={() => setShowPreview(!showPreview)}
              className="w-full px-4 py-2.5 bg-slate-50 hover:bg-slate-100 text-left text-xs font-semibold text-slate-700 flex items-center justify-between transition cursor-pointer"
            >
              <span className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                Extracted Report Preview ({reportText.length} characters)
              </span>
              {showPreview ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </button>
            {showPreview && (
              <div className="p-4 bg-slate-950 text-emerald-400 text-xs font-mono max-h-48 overflow-y-auto whitespace-pre-wrap selection:bg-emerald-900">
                {reportText}
              </div>
            )}
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Patient Details Form */}
        <form onSubmit={handleAnalyze} className="pt-2 border-t border-slate-100">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
            2. Patient Information
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                Patient Name
              </label>
              <input
                type="text"
                required
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                placeholder="e.g. John Doe"
                className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Age</label>
              <input
                type="number"
                min="0"
                max="120"
                required
                value={age}
                onChange={(e) => setAge(e.target.value)}
                className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div className="mt-5 flex items-center justify-between gap-4">
            <div className="text-xs text-slate-500 hidden sm:block">
              Model: <span className="font-semibold text-sky-600">{selectedModel}</span>
            </div>

            <button
              type="submit"
              disabled={loading || extracting || !reportText}
              className="w-full sm:w-auto px-6 py-2.5 bg-sky-500 hover:bg-sky-600 active:bg-sky-700 text-white rounded-xl font-semibold text-sm shadow-md shadow-sky-500/25 flex items-center justify-center gap-2 transition cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Analyzing with Ollama...</span>
                </>
              ) : (
                <>
                  <HeartPulse className="w-4 h-4" />
                  <span>Generate AI Medical Analysis</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AnalysisForm
