import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False, index=True)
    file_type = Column(String(50), default="pdf")
    file_size_bytes = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    metadata_json = Column(JSON, default=dict)

    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="document")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number = Column(Integer, nullable=False, index=True)
    char_count = Column(Integer, default=0)
    text_content = Column(Text, nullable=False)

    document = relationship("Document", back_populates="pages")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    medical_record_number = Column(String(100), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    observations = relationship(
        "Observation", back_populates="patient", cascade="all, delete-orphan"
    )
    analyses = relationship(
        "AnalysisRecord", back_populates="patient", cascade="all, delete-orphan"
    )


class Observation(Base):
    __tablename__ = "observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id = Column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    page_number = Column(Integer, nullable=True)

    code = Column(String(100), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), default="Laboratory", index=True)
    value_raw = Column(String(255), nullable=False)
    numeric_value = Column(Float, nullable=True)
    unit = Column(String(50), default="")
    reference_low = Column(Float, nullable=True)
    reference_high = Column(Float, nullable=True)
    reference_range_text = Column(String(100), nullable=True)
    flag = Column(String(50), default="NORMAL", index=True)
    observation_date = Column(String(50), nullable=True, index=True)  # YYYY-MM-DD or raw string

    confidence = Column(Float, default=0.95)
    text_span = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="observations")
    document = relationship("Document", back_populates="observations")


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_id = Column(String(64), nullable=False, unique=True, index=True)

    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=True)
    prompt_version = Column(String(50), default="v2.0")
    execution_duration_sec = Column(Float, default=0.0)

    structured_result_json = Column(JSON, nullable=False)
    safety_verdict_json = Column(JSON, nullable=False)
    human_review_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    patient = relationship("Patient", back_populates="analyses")


class GuidelineChunkModel(Base):
    __tablename__ = "guideline_chunks"

    id = Column(String(64), primary_key=True)
    knowledge_base_id = Column(String(64), default="clinical-standards-v1", index=True)
    title = Column(String(255), nullable=False)
    organization = Column(String(100), nullable=False, index=True)  # ADA, ACC/AHA, KDIGO, WHO
    category = Column(String(100), nullable=False, index=True)
    section = Column(String(255), nullable=False)
    page = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)
    recommendation_level = Column(String(50), nullable=True)
    publication_year = Column(Integer, default=2024)
    keywords = Column(Text, nullable=True)
    embedding_json = Column(JSON, nullable=True)  # Stored embedding vector for cosine similarity


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    patient_id = Column(String(36), nullable=True, index=True)
    execution_id = Column(String(64), nullable=True, index=True)
    payload_json = Column(JSON, default=dict)
    status = Column(String(50), default="SUCCESS")
