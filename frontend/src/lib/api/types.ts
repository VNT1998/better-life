export interface User {
  id: string
  email: string
  name: string
  created_at?: string
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token?: string
}

export interface Session {
  id: string
  user_id?: string
  title: string
  created_at?: string
}

export interface ChatMessage {
  id?: string
  session_id?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at?: string
}

export interface ModelOption {
  name: string
  model: string
  size?: number
  digest?: string
  details?: Record<string, unknown>
}

export interface ModelsResponse {
  primary: string
  fallbacks: string[]
  available: ModelOption[]
}

export interface ClinicalDocument {
  id: string
  filename: string
  file_type: string
  page_count: number
  created_at: string
  metadata?: Record<string, unknown>
}

export interface ClinicalPatient {
  id: string
  name: string
  age?: number
  gender?: string
  medical_record_number?: string
  created_at: string
}

export interface ObservationDataPoint {
  date: string
  value_raw: string
  numeric_value: number
  unit: string
  flag: string
}

export interface BiomarkerTimeline {
  biomarker: string
  data_points: ObservationDataPoint[]
  trend: 'rising' | 'falling' | 'stable' | 'new' | 'missing'
  clinical_interpretation: string
}

export interface PatientTimelineResponse {
  patient_id: string
  patient_name: string
  timelines: BiomarkerTimeline[]
  overall_trends: Record<string, string>
}

export interface ClinicalAnalysisResult {
  execution_id: string
  patient_id: string
  model_name: string
  structured_result: {
    patient_summary?: Record<string, unknown>
    key_findings?: Array<{
      category: string
      severity: string
      statement: string
      evidence_observations: string[]
      citations: Array<{
        guideline_name: string
        recommendation: string
        similarity_score: number
      }>
    }>
    lifestyle_recommendations?: Array<{
      category: string
      advice: string
      guideline_support: string
    }>
    physician_discussion_points?: string[]
  }
  safety_verdict: {
    passed: boolean
    status: 'PASSED' | 'FLAGGED' | 'REJECTED' | 'REQUIRES_HUMAN_REVIEW'
    violations: string[]
    checks: Record<string, boolean>
    notes: string
  }
  human_review_required: boolean
  audit_logged: boolean
}

export interface KnowledgeBaseItem {
  id: string
  title: string
  organization: string
  category: string
  section: string
  page?: number
  text: string
  recommendation_level?: string
  publication_year: number
}

export interface KnowledgeBaseListResponse {
  knowledge_base_id: string
  name: string
  total_guidelines: number
  guidelines_preview: KnowledgeBaseItem[]
}

export interface AuditEvent {
  id: string
  timestamp: string
  event_type: string
  user_id?: string
  patient_id?: string
  execution_id?: string
  payload?: Record<string, unknown>
  status: string
}
