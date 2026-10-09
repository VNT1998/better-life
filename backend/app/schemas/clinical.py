from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ObservationFlag(StrEnum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    LOW = "LOW"
    CRITICAL_HIGH = "CRITICAL_HIGH"
    CRITICAL_LOW = "CRITICAL_LOW"
    BORDERLINE = "BORDERLINE"
    ABNORMAL = "ABNORMAL"


class TrendDirection(StrEnum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    NEW = "new"
    MISSING = "missing"


class SafetyStatus(StrEnum):
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
    text_content: str | None = None


class DocumentCreate(BaseModel):
    filename: str
    file_type: str = "pdf"
    content_base64: str | None = None


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    page_count: int
    created_at: datetime
    pages: list[DocumentPageSchema] = []
    metadata: dict[str, Any] = {}


# ==========================================
# 2. Patient Schemas
# ==========================================


class PatientCreate(BaseModel):
    id: str | None = None
    name: str
    age: int | None = None
    gender: str | None = None
    medical_record_number: str | None = None


class PatientResponse(BaseModel):
    id: str
    name: str
    age: int | None = None
    gender: str | None = None
    created_at: datetime


# ==========================================
# 3. Structured Clinical Extraction Schemas
# ==========================================


class ObservationValue(BaseModel):
    code: str | None = None
    name: str
    category: str = "Laboratory"  # Hematology, Biochemistry, Lipids, Metabolic, etc.
    value: float | str
    numeric_value: float | None = None
    unit: str = ""
    reference_low: float | None = None
    reference_high: float | None = None
    reference_range_text: str | None = None
    flag: ObservationFlag = ObservationFlag.NORMAL
    interpretation: str | None = None

    # Provenance
    source_document_id: str | None = None
    source_document_name: str | None = None
    page_number: int | None = None
    text_span: str | None = None
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


class MedicationItem(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str | None = None
    status: str = "active"  # active, discontinued, mentioned
    source_document_id: str | None = None
    page_number: int | None = None


class ConditionItem(BaseModel):
    name: str
    status: str = "suspected"  # historical, current, suspected, ruled_out
    notes: str | None = None
    source_document_id: str | None = None
    page_number: int | None = None


class ClinicalExtractionResult(BaseModel):
    patient: dict[str, Any]
    observations: list[ObservationValue] = []
    medications: list[MedicationItem] = []
    conditions: list[ConditionItem] = []
    lab_results: list[ObservationValue] = []
    dates: list[str] = []

    # Model & Execution Metadata
    model_name: str = "unknown"
    model_version: str | None = None
    prompt_version: str = "v2.0"
    execution_id: str
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# 4. Longitudinal Timeline Schemas
# ==========================================


class BiomarkerDataPoint(BaseModel):
    date: str
    value: float | str
    numeric_value: float | None = None
    unit: str
    flag: ObservationFlag
    document_id: str | None = None


class BiomarkerTimeline(BaseModel):
    biomarker_name: str
    category: str
    unit: str
    data_points: list[BiomarkerDataPoint] = []
    trend: TrendDirection = TrendDirection.STABLE
    delta: float | None = None
    percentage_change: float | None = None
    clinical_note: str | None = None


class PatientTimelineResponse(BaseModel):
    patient_id: str
    recorded_dates: list[str]
    timelines: list[BiomarkerTimeline]
    overall_trends: dict[str, str] = {}


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
    page: int | None = None
    text: str
    recommendation_level: str | None = None
    publication_year: int | None = None


class EvidenceCitation(BaseModel):
    claim: str
    guideline_name: str
    organization: str
    section: str
    page: int | None = None
    relevant_excerpt: str
    recommendation_level: str | None = None
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
    category: str | None = None


class RAGQueryResponse(BaseModel):
    query: str
    evidence_chunks: list[GuidelineChunk]
    citations: list[EvidenceCitation]


# ==========================================
# 6. Safety & Clinical Analysis Schemas
# ==========================================


class SafetyCheckResult(BaseModel):
    status: SafetyStatus
    passed: bool
    violations: list[str] = []
    requires_human_review: bool = False
    checks: dict[str, bool] = {
        "no_prescriptions": True,
        "no_definitive_diagnosis": True,
        "no_irreversible_decisions": True,
        "citations_grounded": True,
        "confidence_threshold_met": True,
    }
    notes: str | None = None


class FindingWithEvidence(BaseModel):
    finding: str
    category: str
    risk_level: str  # Low, Medium, High, Borderline
    clinical_rationale: str
    citations: list[EvidenceCitation] = []


class AnalysisResultResponse(BaseModel):
    id: str
    patient_id: str
    execution_id: str
    document_ids: list[str] = []
    created_at: datetime

    # MLOps Provenance
    model_name: str
    model_version: str | None = None
    prompt_version: str
    execution_duration_sec: float = 0.0

    # Structured Results
    extracted_data: ClinicalExtractionResult
    timeline_summary: dict[str, Any] | None = None
    findings: list[FindingWithEvidence] = []
    dietary_lifestyle_recommendations: list[str] = []
    recommended_follow_up_tests: list[str] = []

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
    user_id: str | None = None
    patient_id: str | None = None
    execution_id: str | None = None
    payload: dict[str, Any] = {}
    status: str = "SUCCESS"


class AuditEventResponse(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    user_id: str | None = None
    patient_id: str | None = None
    execution_id: str | None = None
    payload: dict[str, Any] = {}
    status: str
