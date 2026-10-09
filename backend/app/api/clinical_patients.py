import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models import Patient
from app.db.session import get_db
from app.schemas.clinical import (
    AnalysisResultResponse,
    PatientCreate,
    PatientResponse,
    PatientTimelineResponse,
)
from app.services.audit_service import audit_service
from app.services.orchestrator_service import clinical_orchestrator
from app.services.timeline_service import timeline_service

router = APIRouter(prefix="/patients", tags=["patients"])


class PatientAnalyzeRequest(BaseModel):
    document_id: str
    model: str | None = None
    user_id: str | None = "clinical-analyst"


@router.post("", response_model=PatientResponse)
def create_patient(req: PatientCreate, db: Session = Depends(get_db)):
    """Creates a new patient profile for longitudinal analysis."""
    patient_id = req.id or str(uuid.uuid4())
    patient = Patient(
        id=patient_id,
        name=req.name,
        age=req.age,
        gender=req.gender,
        medical_record_number=req.medical_record_number,
    )
    db.add(patient)
    db.commit()

    audit_service.log_event(
        event_type="PATIENT_CREATED",
        patient_id=patient.id,
        payload={"name": req.name, "age": req.age, "gender": req.gender},
        db_session=db,
    )

    return PatientResponse(
        id=patient.id,
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        created_at=patient.created_at,
    )


@router.get("", response_model=list[PatientResponse])
def list_patients(db: Session = Depends(get_db)):
    """Lists all enrolled patients."""
    patients = db.query(Patient).order_by(Patient.created_at.desc()).all()
    return [
        PatientResponse(
            id=p.id,
            name=p.name,
            age=p.age,
            gender=p.gender,
            created_at=p.created_at,
        )
        for p in patients
    ]


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Fetches demographic profile for a patient."""
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return PatientResponse(
        id=p.id,
        name=p.name,
        age=p.age,
        gender=p.gender,
        created_at=p.created_at,
    )


@router.post("/{patient_id}/analyze", response_model=AnalysisResultResponse)
async def analyze_patient(
    patient_id: str,
    req: PatientAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Executes the end-to-end Clinical Evidence Intelligence pipeline:
    Document Segmentation -> Structured Extraction -> Longitudinal Timeline -> Evidence RAG -> Deterministic Safety Gate -> Audit Trail.
    """
    try:
        result = await clinical_orchestrator.analyze_patient_document_async(
            patient_id=patient_id,
            document_id=req.document_id,
            user_id=req.user_id,
            model=req.model,
            db_session=db,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clinical analysis pipeline error: {e!s}",
        ) from e


@router.get("/{patient_id}/timeline", response_model=PatientTimelineResponse)
def get_patient_timeline(patient_id: str, db: Session = Depends(get_db)):
    """
    Retrieves longitudinal biomarker progression, comparing observations over time
    and classifying trajectories as rising, falling, stable, new, or missing.
    """
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    timeline = timeline_service.get_patient_timeline(patient_id=patient_id, db_session=db)
    return timeline
