from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import AnalysisRecord

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.get("/{analysis_id}")
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Fetches full clinical intelligence analysis record by ID."""
    rec = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis record not found")

    return {
        "id": rec.id,
        "patient_id": rec.patient_id,
        "execution_id": rec.execution_id,
        "model_name": rec.model_name,
        "model_version": rec.model_version,
        "prompt_version": rec.prompt_version,
        "execution_duration_sec": rec.execution_duration_sec,
        "structured_result": rec.structured_result_json,
        "safety_verdict": rec.safety_verdict_json,
        "human_review_required": rec.human_review_required,
        "created_at": rec.created_at,
    }


@router.get("")
def list_analyses(patient_id: str = None, db: Session = Depends(get_db)):
    """Lists historical clinical analyses."""
    q = db.query(AnalysisRecord)
    if patient_id:
        q = q.filter(AnalysisRecord.patient_id == patient_id)
    records = q.order_by(AnalysisRecord.created_at.desc()).limit(50).all()

    return [
        {
            "id": r.id,
            "patient_id": r.patient_id,
            "execution_id": r.execution_id,
            "model_name": r.model_name,
            "safety_verdict": r.safety_verdict_json.get("status") if r.safety_verdict_json else "UNKNOWN",
            "human_review_required": r.human_review_required,
            "created_at": r.created_at,
        }
        for r in records
    ]
