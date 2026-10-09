import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.db.session import SessionLocal
from app.db.models import Patient, Document, Observation, AnalysisRecord
from app.schemas.clinical import (
    AnalysisResultResponse,
    ClinicalExtractionResult,
    FindingWithEvidence,
    ObservationFlag,
)
from app.agents.extraction_agent import extraction_agent
from app.services.timeline_service import timeline_service
from app.services.knowledge_base_service import knowledge_base_service
from app.services.safety_service import safety_service
from app.services.audit_service import audit_service
from app.services.nuvorix_adapter import nuvorix_adapter

logger = logging.getLogger(__name__)


class ClinicalOrchestratorService:
    """
    End-to-End Orchestrator for Clinical Evidence Intelligence.
    Coordinates document extraction, longitudinal timeline modeling, evidence RAG,
    safety gating, and audit logging.
    """

    async def analyze_patient_document_async(
        self,
        patient_id: str,
        document_id: str,
        user_id: Optional[str] = "demo-user",
        model: Optional[str] = None,
        db_session: Optional[Any] = None,
    ) -> AnalysisResultResponse:
        start_time = time.time()
        execution_id = f"exec-{uuid.uuid4().hex[:12]}"

        should_close = False
        db = db_session
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            # 1. Fetch Patient and Document
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                raise ValueError(f"Patient with ID {patient_id} not found.")

            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document with ID {document_id} not found.")

            # Audit: Ingestion Triggered
            audit_service.log_event(
                event_type="CLINICAL_ANALYSIS_STARTED",
                user_id=user_id,
                patient_id=patient_id,
                execution_id=execution_id,
                payload={"document_id": document_id, "filename": document.filename},
                db_session=db,
            )

            # 2. Structured Extraction
            pages_data = [
                {"page_number": p.page_number, "text_content": p.text_content}
                for p in document.pages
            ]
            patient_hint = {"id": patient.id, "name": patient.name, "age": patient.age, "gender": patient.gender}

            extracted_result: ClinicalExtractionResult = await extraction_agent.extract_from_pages_async(
                pages=pages_data,
                document_id=document.id,
                document_name=document.filename,
                patient_hint=patient_hint,
                model=model,
            )

            # 3. Store Extracted Observations in Database
            obs_date = extracted_result.dates[0] if extracted_result.dates else datetime.utcnow().strftime("%Y-%m-%d")
            for obs in extracted_result.observations:
                obs_record = Observation(
                    id=str(uuid.uuid4()),
                    patient_id=patient.id,
                    document_id=document.id,
                    page_number=obs.page_number,
                    code=obs.code,
                    name=obs.name,
                    category=obs.category,
                    value_raw=str(obs.value),
                    numeric_value=obs.numeric_value,
                    unit=obs.unit,
                    reference_low=obs.reference_low,
                    reference_high=obs.reference_high,
                    reference_range_text=obs.reference_range_text,
                    flag=obs.flag.value,
                    observation_date=obs_date,
                    confidence=obs.confidence,
                    text_span=obs.text_span,
                )
                db.add(obs_record)
            db.commit()

            # 4. Compute Longitudinal Timeline
            timeline_response = timeline_service.get_patient_timeline(patient_id=patient.id, db_session=db)

            # 5. Evidence RAG Retrieval & Finding Grounding
            findings: List[FindingWithEvidence] = knowledge_base_service.ground_observations_with_evidence(
                observations=extracted_result.observations,
                db_session=db,
            )

            # 6. Generate Educational Lifestyle & Testing Guidance
            lifestyle_guidance, follow_up_tests = self._synthesize_guidance(extracted_result.observations)

            # 7. Deterministic Safety Validation
            findings_summary_text = "\n".join(f"{f.finding}: {f.clinical_rationale}" for f in findings)
            all_citations = [c for f in findings for c in f.citations]

            safety_verdict = safety_service.validate_clinical_safety(
                observations=extracted_result.observations,
                findings_text=findings_summary_text,
                citations=all_citations,
            )

            duration_sec = time.time() - start_time

            # 8. Save Analysis Record
            analysis_id = str(uuid.uuid4())
            analysis_record = AnalysisRecord(
                id=analysis_id,
                patient_id=patient.id,
                execution_id=execution_id,
                model_name=extracted_result.model_name,
                model_version=extracted_result.model_version,
                prompt_version=extracted_result.prompt_version,
                execution_duration_sec=duration_sec,
                structured_result_json={
                    "extracted_count": len(extracted_result.observations),
                    "findings_count": len(findings),
                    "dates": extracted_result.dates,
                },
                safety_verdict_json=safety_verdict.model_dump(),
                human_review_required=safety_verdict.requires_human_review,
            )
            db.add(analysis_record)
            db.commit()

            # 9. Log Audit Trail
            audit_service.log_event(
                event_type="CLINICAL_ANALYSIS_COMPLETED",
                user_id=user_id,
                patient_id=patient_id,
                execution_id=execution_id,
                payload={
                    "analysis_id": analysis_id,
                    "safety_status": safety_verdict.status.value,
                    "findings_count": len(findings),
                    "citations_count": len(all_citations),
                    "duration_sec": round(duration_sec, 2),
                },
                status="SUCCESS" if safety_verdict.passed else "FLAGGED",
                db_session=db,
            )

            # 10. Register Nuvorix Reference Run
            nuvorix_adapter.register_execution_run(
                execution_id=execution_id,
                patient_id=patient.id,
                model_name=extracted_result.model_name,
                model_version=extracted_result.model_version or "1.0",
                prompt_version=extracted_result.prompt_version,
                duration_sec=duration_sec,
                findings_count=len(findings),
                citations_count=len(all_citations),
                safety_status=safety_verdict.status.value,
            )

            return AnalysisResultResponse(
                id=analysis_id,
                patient_id=patient.id,
                execution_id=execution_id,
                document_ids=[document.id],
                created_at=datetime.utcnow(),
                model_name=extracted_result.model_name,
                model_version=extracted_result.model_version,
                prompt_version=extracted_result.prompt_version,
                execution_duration_sec=duration_sec,
                extracted_data=extracted_result,
                timeline_summary=timeline_response.overall_trends,
                findings=findings,
                dietary_lifestyle_recommendations=lifestyle_guidance,
                recommended_follow_up_tests=follow_up_tests,
                safety_verdict=safety_verdict,
                human_review_required=safety_verdict.requires_human_review,
            )

        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Error executing clinical analysis pipeline: {e}")
            audit_service.log_event(
                event_type="CLINICAL_ANALYSIS_FAILED",
                user_id=user_id,
                patient_id=patient_id,
                execution_id=execution_id,
                payload={"error": str(e)},
                status="ERROR",
                db_session=db,
            )
            raise e
        finally:
            if should_close and db:
                db.close()

    def _synthesize_guidance(self, observations: List[Any]) -> tuple[List[str], List[str]]:
        guidance: List[str] = []
        tests: List[str] = []

        obs_names = {o.name.lower(): o for o in observations}

        # Metabolic & Glucose
        if any("glucose" in k or "sugar" in k or "hba1c" in k for k in obs_names):
            guidance.append("Maintain consistent meal timings, prioritize whole grains with soluble fiber, and monitor glycemic response.")
            tests.append("Repeat Fasting Blood Sugar and 3-month Glycated Hemoglobin (HbA1c) monitoring.")

        # Lipids & Cardiovascular
        if any("cholesterol" in k or "triglyceride" in k or "ldl" in k for k in obs_names):
            guidance.append("Emphasize a cardioprotective diet: reduce saturated and trans fats, increase omega-3 fatty acids, and incorporate regular aerobic activity.")
            tests.append("Comprehensive Lipid Profile recheck in 8 to 12 weeks.")

        # Hematology & Anemia
        if any("hemoglobin" in k or "wbc" in k or "platelet" in k for k in obs_names):
            guidance.append("Ensure adequate dietary intake of iron, vitamin B12, and folate; maintain optimal hydration.")
            tests.append("Confirmatory Complete Blood Count (CBC) with peripheral smear and serum ferritin.")

        # Renal / Kidney
        if any("creatinine" in k or "bun" in k for k in obs_names):
            guidance.append("Ensure adequate hydration throughout the day; exercise caution with regular non-steroidal anti-inflammatory drugs (NSAIDs).")
            tests.append("Renal Function Panel and Urine Albumin-to-Creatinine Ratio (uACR).")

        if not guidance:
            guidance.append("Continue balanced lifestyle with regular physical exercise, adequate restorative sleep, and nutritional diversity.")
            tests.append("Routine annual comprehensive health checkup.")

        return guidance, tests


clinical_orchestrator = ClinicalOrchestratorService()
