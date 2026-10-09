from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class ObservationFlag(str, Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    LOW = "LOW"
    CRITICAL_HIGH = "CRITICAL_HIGH"
    CRITICAL_LOW = "CRITICAL_LOW"
    BORDERLINE = "BORDERLINE"
    ABNORMAL = "ABNORMAL"


class TrendDirection(str, Enum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    NEW = "new"
    MISSING = "missing"


class SafetyStatus(str, Enum):
    PASSED = "PASSED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


# ==========================================
# 1. Document Schemas
# ==========================================

class DocumentPageSchema(BaseModel):
    page_number: int
    char_count: int
    text_preview: str
    text_content: Optional[str] = None


class DocumentCreate(BaseModel):
    filename: str
    file_type: str = "pdf"
    content_base64: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    page_count: int
    created_at: datetime
    pages: List[DocumentPageSchema] = []
    metadata: Dict[str, Any] = {}


# ==========================================
# 2. Patient Schemas
# ==========================================

class PatientCreate(BaseModel):
    id: Optional[str] = None
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_record_number: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    created_at: datetime


# ==========================================
# 3. Structured Clinical Extraction Schemas
# ==========================================

class ObservationValue(BaseModel):
    code: Optional[str] = None
    name: str
    category: str = "Laboratory"  # Hematology, Biochemistry, Lipids, Metabolic, etc.
    value: Union[float, str]
    numeric_value: Optional[float] = None
    unit: str = ""
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    reference_range_text: Optional[str] = None
    flag: ObservationFlag = ObservationFlag.NORMAL
    interpretation: Optional[str] = None

    # Provenance
    source_document_id: Optional[str] = None
    source_document_name: Optional[str] = None
    page_number: Optional[int] = None
    text_span: Optional[str] = None
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


class MedicationItem(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    status: str = "active"  # active, discontinued, mentioned
    source_document_id: Optional[str] = None
    page_number: Optional[int] = None


class ConditionItem(BaseModel):
    name: str
    status: str = "suspected"  # historical, current, suspected, ruled_out
    notes: Optional[str] = None
    source_document_id: Optional[str] = None
    page_number: Optional[int] = None


class ClinicalExtractionResult(BaseModel):
    patient: Dict[str, Any]
    observations: List[ObservationValue] = []
    medications: List[MedicationItem] = []
    conditions: List[ConditionItem] = []
    lab_results: List[ObservationValue] = []
    dates: List[str] = []

    # Model & Execution Metadata
    model_name: str = "unknown"
    model_version: Optional[str] = None
    prompt_version: str = "v2.0"
    execution_id: str
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# 4. Longitudinal Timeline Schemas
# ==========================================

class BiomarkerDataPoint(BaseModel):
    date: str
    value: Union[float, str]
    numeric_value: Optional[float] = None
    unit: str
    flag: ObservationFlag
    document_id: Optional[str] = None


class BiomarkerTimeline(BaseModel):
    biomarker_name: str
    category: str
    unit: str
    data_points: List[BiomarkerDataPoint] = []
    trend: TrendDirection = TrendDirection.STABLE
    delta: Optional[float] = None
    percentage_change: Optional[float] = None
    clinical_note: Optional[str] = None


class PatientTimelineResponse(BaseModel):
    patient_id: str
    recorded_dates: List[str]
    timelines: List[BiomarkerTimeline]
    overall_trends: Dict[str, str] = {}


# ==========================================
# 5. Evidence RAG Schemas
# ==========================================

class GuidelineChunk(BaseModel):
    id: str
    knowledge_base_id: str
    title: str
    organization: str  # e.g. "ADA", "ACC/AHA", "KDIGO", "WHO"
    category: str
    section: str
    page: Optional[int] = None
    text: str
    recommendation_level: Optional[str] = None
    publication_year: Optional[int] = None


class EvidenceCitation(BaseModel):
    claim: str
    guideline_name: str
    organization: str
    section: str
    page: Optional[int] = None
    relevant_excerpt: str
    recommendation_level: Optional[str] = None
    similarity_score: float = 0.0


class KnowledgeBaseCreate(BaseModel):
    id: str
    name: str
    description: str
    version: str = "2026.1"


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    chunk_count: int


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 4
    category: Optional[str] = None


class RAGQueryResponse(BaseModel):
    query: str
    evidence_chunks: List[GuidelineChunk]
    citations: List[EvidenceCitation]


# ==========================================
# 6. Safety & Clinical Analysis Schemas
# ==========================================

class SafetyCheckResult(BaseModel):
    status: SafetyStatus
    passed: bool
    violations: List[str] = []
    requires_human_review: bool = False
    checks: Dict[str, bool] = {
        "no_prescriptions": True,
        "no_definitive_diagnosis": True,
        "no_irreversible_decisions": True,
        "citations_grounded": True,
        "confidence_threshold_met": True,
    }
    notes: Optional[str] = None


class FindingWithEvidence(BaseModel):
    finding: str
    category: str
    risk_level: str  # Low, Medium, High, Borderline
    clinical_rationale: str
    citations: List[EvidenceCitation] = []


class AnalysisResultResponse(BaseModel):
    id: str
    patient_id: str
    execution_id: str
    document_ids: List[str] = []
    created_at: datetime

    # MLOps Provenance
    model_name: str
    model_version: Optional[str] = None
    prompt_version: str
    execution_duration_sec: float = 0.0

    # Structured Results
    extracted_data: ClinicalExtractionResult
    timeline_summary: Optional[Dict[str, Any]] = None
    findings: List[FindingWithEvidence] = []
    dietary_lifestyle_recommendations: List[str] = []
    recommended_follow_up_tests: List[str] = []

    # Safety Verdict
    safety_verdict: SafetyCheckResult
    human_review_required: bool = False

    # Disclaimer
    disclaimer: str = (
        "This analysis is generated by AI for educational and clinical research demonstration purposes only. "
        "It does not constitute medical diagnosis, treatment advice, or formal clinical decision support. "
        "Always consult a qualified healthcare professional."
    )


# ==========================================
# 7. Audit Trail Schemas
# ==========================================

class AuditEventCreate(BaseModel):
    event_type: str
    user_id: Optional[str] = None
    patient_id: Optional[str] = None
    execution_id: Optional[str] = None
    payload: Dict[str, Any] = {}
    status: str = "SUCCESS"


class AuditEventResponse(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    user_id: Optional[str] = None
    patient_id: Optional[str] = None
    execution_id: Optional[str] = None
    payload: Dict[str, Any] = {}
    status: str
