from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.clinical import AuditEventResponse
from app.services.audit_service import audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", response_model=list[AuditEventResponse])
def get_audit_events(
    patient_id: str | None = Query(None, description="Filter events by patient ID"),
    event_type: str | None = Query(None, description="Filter events by type"),
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
    db: Session = Depends(get_db),
):
    """
    Returns the immutable audit log of document uploads, extractions,
    safety gate evaluations, and human review decisions.
    """
    events = audit_service.query_events(
        patient_id=patient_id,
        event_type=event_type,
        limit=limit,
        db_session=db,
    )
    return events
