import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.db.session import SessionLocal
from app.db.models import AuditEventModel
from app.schemas.clinical import AuditEventResponse, AuditEventCreate

logger = logging.getLogger(__name__)


class AuditService:
    """
    Audit Trail & Provenance Event Logging Service.
    Maintains tamper-evident records of all system executions, data access, and safety gates.
    """

    def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        db_session: Optional[Any] = None,
    ) -> AuditEventResponse:
        should_close = False
        db = db_session
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            event_id = str(uuid.uuid4())
            now = datetime.utcnow()
            record = AuditEventModel(
                id=event_id,
                timestamp=now,
                event_type=event_type,
                user_id=user_id,
                patient_id=patient_id,
                execution_id=execution_id,
                payload_json=payload or {},
                status=status,
            )
            db.add(record)
            db.commit()

            return AuditEventResponse(
                id=event_id,
                timestamp=now,
                event_type=event_type,
                user_id=user_id,
                patient_id=patient_id,
                execution_id=execution_id,
                payload=payload or {},
                status=status,
            )
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Failed to record audit event {event_type}: {e}")
            return AuditEventResponse(
                id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                event_type=event_type,
                user_id=user_id,
                patient_id=patient_id,
                execution_id=execution_id,
                payload=payload or {},
                status="FAILED",
            )
        finally:
            if should_close and db:
                db.close()

    def query_events(
        self,
        patient_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
        db_session: Optional[Any] = None,
    ) -> List[AuditEventResponse]:
        should_close = False
        db = db_session
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            q = db.query(AuditEventModel)
            if patient_id:
                q = q.filter(AuditEventModel.patient_id == patient_id)
            if event_type:
                q = q.filter(AuditEventModel.event_type == event_type)

            records = q.order_by(AuditEventModel.timestamp.desc()).limit(limit).all()

            return [
                AuditEventResponse(
                    id=r.id,
                    timestamp=r.timestamp,
                    event_type=r.event_type,
                    user_id=r.user_id,
                    patient_id=r.patient_id,
                    execution_id=r.execution_id,
                    payload=r.payload_json or {},
                    status=r.status,
                )
                for r in records
            ]
        finally:
            if should_close and db:
                db.close()


audit_service = AuditService()
