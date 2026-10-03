from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from api.deps import auth_service, ai_service, get_current_user
from config.prompts import SPECIALIST_PROMPTS
from config.sample_data import SAMPLE_REPORT
from utils.pdf_extractor import extract_text_from_pdf

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    session_id: str
    patient_name: str
    age: int
    gender: str
    report_text: str
    model: Optional[str] = None


@router.get("/sample-report")
def get_sample_report():
    return {"report": SAMPLE_REPORT}


@router.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a PDF document",
        )

    content = await file.read()
    extracted = extract_text_from_pdf(content, filename=file.filename)

    if isinstance(extracted, str) and (
        extracted.startswith("File size exceeds")
        or extracted.startswith("Invalid file type")
        or extracted.startswith("Could not extract")
        or extracted.startswith("The uploaded file")
        or extracted.startswith("Error extracting")
        or extracted.startswith("Extracted text is too short")
        or extracted.startswith("PDF exceeds")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=extracted,
        )

    return {"success": True, "text": extracted, "filename": file.filename}


@router.post("")
async def run_analysis(
    req: AnalysisRequest, user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = user["id"]

    # Validate inputs
    if not req.patient_name or req.age < 0 or not req.gender or not req.report_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient name, age, gender, and report text are all required",
        )

    # Check rate limit
    can_analyze, error_msg = ai_service.check_rate_limit(user_id)
    if not can_analyze:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg or "Daily analysis limit reached",
        )

    # 1. Save user action message
    auth_service.save_chat_message(
        session_id=req.session_id,
        content=f"Analyzing blood report for patient: **{req.patient_name}** ({req.age} y/o, {req.gender})",
        role="user",
    )

    # 2. Run analysis using Ollama via AIService
    payload = {
        "patient_name": req.patient_name,
        "age": req.age,
        "gender": req.gender,
        "report": req.report_text,
    }

    result = await ai_service.generate_analysis_async(
        data=payload,
        system_prompt=SPECIALIST_PROMPTS["comprehensive_analyst"],
        user_id=user_id,
        model=req.model,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Analysis failed"),
        )

    # 3. Store report text as system message for follow-up chat retrieval
    report_metadata = f"__REPORT_TEXT__\n{req.report_text}\n__END_REPORT_TEXT__"
    auth_service.save_chat_message(
        session_id=req.session_id,
        content=report_metadata,
        role="system",
    )

    # 4. Save analysis response message
    analysis_content = result.get("content", "")
    model_used = result.get("model_used")
    if model_used:
        analysis_content += f"\n\n*Analysis generated using Ollama model `{model_used}`*"

    assistant_msg = auth_service.save_chat_message(
        session_id=req.session_id,
        content=analysis_content,
        role="assistant",
    )

    remaining_limit = ai_service.get_remaining_limit(user_id)

    return {
        "success": True,
        "content": analysis_content,
        "model_used": model_used,
        "remaining_limit": remaining_limit,
        "message": assistant_msg[1] if isinstance(assistant_msg, tuple) else assistant_msg,
    }
