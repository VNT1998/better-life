from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.api.deps import ai_service, auth_service, get_current_user
from app.config import (
    APP_NAME,
    APP_TAGLINE,
    APP_DESCRIPTION,
    APP_ICON,
    MAX_UPLOAD_SIZE_MB,
    MAX_PDF_PAGES,
    ANALYSIS_DAILY_LIMIT,
    OLLAMA_BASE_URL,
    OLLAMA_PRIMARY_MODEL,
    OLLAMA_FALLBACK_MODELS,
)

router = APIRouter(tags=["config"])


@router.get("/models")
async def get_models():
    models = await ai_service.get_available_models()
    return {
        "primary_model": OLLAMA_PRIMARY_MODEL,
        "fallback_models": OLLAMA_FALLBACK_MODELS,
        "endpoint": OLLAMA_BASE_URL,
        "available_models": models,
    }


@router.get("/config")
def get_config(user: Dict[str, Any] = Depends(get_current_user)):
    user_id = user.get("id", "default")
    remaining = ai_service.get_remaining_limit(user_id)
    return {
        "app_name": APP_NAME,
        "app_tagline": APP_TAGLINE,
        "app_description": APP_DESCRIPTION,
        "app_icon": APP_ICON,
        "max_upload_size_mb": MAX_UPLOAD_SIZE_MB,
        "max_pdf_pages": MAX_PDF_PAGES,
        "daily_limit": ANALYSIS_DAILY_LIMIT,
        "remaining_limit": remaining,
        "is_supabase_connected": auth_service.is_supabase_ready,
        "ollama_endpoint": OLLAMA_BASE_URL,
        "primary_model": OLLAMA_PRIMARY_MODEL,
    }
