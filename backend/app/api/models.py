from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import ai_service, auth_service, get_current_user
from app.config import (
    ANALYSIS_DAILY_LIMIT,
    APP_DESCRIPTION,
    APP_ICON,
    APP_NAME,
    APP_TAGLINE,
    MAX_PDF_PAGES,
    MAX_UPLOAD_SIZE_MB,
    OLLAMA_BASE_URL,
    OLLAMA_FALLBACK_MODELS,
    OLLAMA_PRIMARY_MODEL,
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
def get_config(user: dict[str, Any] = Depends(get_current_user)):
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
        "supabase_status": auth_service.supabase_status,
        "supabase_error": auth_service.supabase_error,
        "ollama_endpoint": OLLAMA_BASE_URL,
        "primary_model": OLLAMA_PRIMARY_MODEL,
    }
