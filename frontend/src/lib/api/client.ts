import { env } from '@/lib/env'
import type {
  User,
  AuthResponse,
  Session,
  ChatMessage,
  ModelsResponse,
  ClinicalDocument,
  ClinicalPatient,
  PatientTimelineResponse,
  ClinicalAnalysisResult,
  KnowledgeBaseListResponse,
  AuditEvent,
} from './types'

const API_BASE = env.VITE_API_BASE_URL || '/api'

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('health_auth_token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

async function handleResponse<T>(res: Response, defaultErrorMsg: string): Promise<T> {
  if (!res.ok) {
    let errorDetail = defaultErrorMsg
    try {
      const data = await res.json()
      errorDetail = data.error?.message || data.detail || defaultErrorMsg
    } catch {
      // JSON parse failed, use default error message
    }
    throw new Error(errorDetail)
  }
  return res.json() as Promise<T>
}

export const api = {
  // ==========================================
  // Authentication
  // ==========================================
  async signup(name: string, email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    })
    return handleResponse<AuthResponse>(res, 'Signup failed')
  },

  async signin(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    return handleResponse<AuthResponse>(res, 'Login failed')
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders(),
    })
    const data = await handleResponse<{ user: User }>(res, 'Failed to fetch user')
    return data.user
  },

  async signout(): Promise<void> {
    await fetch(`${API_BASE}/auth/signout`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
  },

  // ==========================================
  // Chat Sessions
  // ==========================================
  async getSessions(): Promise<Session[]> {
    const res = await fetch(`${API_BASE}/sessions`, {
      headers: getAuthHeaders(),
    })
    if (!res.ok) return []
    return res.json()
  },

  async createSession(title: string): Promise<Session> {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ title }),
    })
    return handleResponse<Session>(res, 'Failed to create session')
  },

  async deleteSession(sessionId: string): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    return handleResponse<{ success: boolean }>(res, 'Failed to delete session')
  },

  async getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`, {
      headers: getAuthHeaders(),
    })
    if (!res.ok) return []
    return res.json()
  },

  // ==========================================
  // Blood Report Analysis & PDF
  // ==========================================
  async getSampleReport(): Promise<string> {
    const res = await fetch(`${API_BASE}/analysis/sample-report`)
    const data = await handleResponse<{ report: string }>(res, 'Failed to fetch sample report')
    return data.report
  },

  async extractPdf(file: File): Promise<string> {
    const formData = new FormData()
    formData.append('file', file)
    const token = localStorage.getItem('health_auth_token')
    const headers: Record<string, string> = {}
    if (token) headers['Authorization'] = `Bearer ${token}`

    const res = await fetch(`${API_BASE}/analysis/extract-pdf`, {
      method: 'POST',
      headers,
      body: formData,
    })
    const data = await handleResponse<{ text: string }>(res, 'PDF extraction failed')
    return data.text
  },

  async runAnalysis(params: {
    sessionId: string
    patientName: string
    age: string | number
    gender: string
    reportText: string
    model?: string
  }): Promise<{ success: boolean; analysis: string; session_id: string }> {
    const res = await fetch(`${API_BASE}/analysis`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        session_id: params.sessionId,
        patient_name: params.patientName,
        age: typeof params.age === 'number' ? params.age : parseInt(params.age, 10),
        gender: params.gender,
        report_text: params.reportText,
        model: params.model,
      }),
    })
    return handleResponse<{ success: boolean; analysis: string; session_id: string }>(
      res,
      'Analysis failed'
    )
  },

  // ==========================================
  // Chat & Streaming
  // ==========================================
  async sendChatMessage(params: {
    sessionId: string
    query: string
    model?: string
  }): Promise<{ success: boolean; content: string; model_used?: string }> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        session_id: params.sessionId,
        query: params.query,
        model: params.model,
      }),
    })
    return handleResponse<{ success: boolean; content: string; model_used?: string }>(
      res,
      'Failed to send chat message'
    )
  },

  async streamChatMessage(
    params: {
      sessionId: string
      query: string
      model?: string
    },
    onChunk: (token: string, done: boolean) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        session_id: params.sessionId,
        query: params.query,
        model: params.model,
      }),
      signal,
    })

    if (!res.ok || !res.body) {
      throw new Error('Streaming failed to initiate')
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6))
            onChunk(data.token || '', Boolean(data.done))
          } catch {
            // Ignore partial SSE JSON chunks
          }
        }
      }
    }
  },

  // ==========================================
  // Models & System Config
  // ==========================================
  async getModels(): Promise<ModelsResponse | null> {
    const res = await fetch(`${API_BASE}/models`)
    if (!res.ok) return null
    return res.json()
  },

  async getConfig(): Promise<Record<string, unknown> | null> {
    const res = await fetch(`${API_BASE}/config`, {
      headers: getAuthHeaders(),
    })
    if (!res.ok) return null
    return res.json()
  },

  // ==========================================
  // Clinical Evidence Intelligence Platform
  // ==========================================
  async uploadClinicalDocument(file: File): Promise<ClinicalDocument> {
    const formData = new FormData()
    formData.append('file', file)
    const token = localStorage.getItem('health_auth_token')
    const headers: Record<string, string> = {}
    if (token) headers['Authorization'] = `Bearer ${token}`

    const res = await fetch(`${API_BASE}/documents`, {
      method: 'POST',
      headers,
      body: formData,
    })
    return handleResponse<ClinicalDocument>(res, 'Document upload failed')
  },

  async listClinicalDocuments(): Promise<ClinicalDocument[]> {
    const res = await fetch(`${API_BASE}/documents`)
    if (!res.ok) return []
    return res.json()
  },

  async getClinicalDocument(docId: string): Promise<ClinicalDocument> {
    const res = await fetch(`${API_BASE}/documents/${docId}`)
    return handleResponse<ClinicalDocument>(res, 'Document not found')
  },

  async createClinicalPatient(patientData: {
    name: string
    age?: number
    gender?: string
    medical_record_number?: string
  }): Promise<ClinicalPatient> {
    const res = await fetch(`${API_BASE}/patients`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(patientData),
    })
    return handleResponse<ClinicalPatient>(res, 'Failed to create patient')
  },

  async listClinicalPatients(): Promise<ClinicalPatient[]> {
    const res = await fetch(`${API_BASE}/patients`, {
      headers: getAuthHeaders(),
    })
    if (!res.ok) return []
    return res.json()
  },

  async getClinicalPatient(patientId: string): Promise<ClinicalPatient> {
    const res = await fetch(`${API_BASE}/patients/${patientId}`)
    return handleResponse<ClinicalPatient>(res, 'Patient not found')
  },

  async analyzeClinicalPatient(
    patientId: string,
    documentId: string,
    model?: string
  ): Promise<ClinicalAnalysisResult> {
    const res = await fetch(`${API_BASE}/patients/${patientId}/analyze`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        document_id: documentId,
        model: model || undefined,
      }),
    })
    return handleResponse<ClinicalAnalysisResult>(res, 'Clinical analysis pipeline failed')
  },

  async getClinicalPatientTimeline(patientId: string): Promise<PatientTimelineResponse> {
    const res = await fetch(`${API_BASE}/patients/${patientId}/timeline`)
    return handleResponse<PatientTimelineResponse>(res, 'Timeline retrieval failed')
  },

  async listKnowledgeBases(): Promise<KnowledgeBaseListResponse[]> {
    const res = await fetch(`${API_BASE}/knowledge-bases`)
    if (!res.ok) return []
    return res.json()
  },

  async queryKnowledgeBase(
    kbId: string,
    query: string,
    topK = 4
  ): Promise<{ query: string; matched_guidelines: unknown[]; total_matches: number }> {
    const res = await fetch(`${API_BASE}/knowledge-bases/${kbId}/query`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query, top_k: topK }),
    })
    return handleResponse<{ query: string; matched_guidelines: unknown[]; total_matches: number }>(
      res,
      'Knowledge base query failed'
    )
  },

  async getAnalysisRecord(analysisId: string): Promise<ClinicalAnalysisResult> {
    const res = await fetch(`${API_BASE}/analyses/${analysisId}`)
    return handleResponse<ClinicalAnalysisResult>(res, 'Analysis record not found')
  },

  async listAnalysisRecords(patientId?: string): Promise<ClinicalAnalysisResult[]> {
    const url = patientId ? `${API_BASE}/analyses?patient_id=${patientId}` : `${API_BASE}/analyses`
    const res = await fetch(url)
    if (!res.ok) return []
    return res.json()
  },

  async getAuditEvents(patientId?: string, eventType?: string, limit = 50): Promise<AuditEvent[]> {
    let url = `${API_BASE}/audit/events?limit=${limit}`
    if (patientId) url += `&patient_id=${patientId}`
    if (eventType) url += `&event_type=${eventType}`
    const res = await fetch(url)
    if (!res.ok) return []
    return res.json()
  },
}
