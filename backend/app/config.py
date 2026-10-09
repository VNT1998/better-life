"""
Legacy configuration adapter re-exporting typed settings from app.core.config.
"""

from app.core.config import settings

APP_NAME = settings.APP_NAME
APP_DESCRIPTION = settings.APP_DESCRIPTION
APP_ICON = settings.APP_ICON
APP_TAGLINE = settings.APP_TAGLINE

MAX_UPLOAD_SIZE_MB = settings.MAX_UPLOAD_SIZE_MB
MAX_PDF_PAGES = settings.MAX_PDF_PAGES
SESSION_TIMEOUT_MINUTES = settings.SESSION_TIMEOUT_MINUTES
ANALYSIS_DAILY_LIMIT = settings.ANALYSIS_DAILY_LIMIT

OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL.rstrip("/")
OLLAMA_PRIMARY_MODEL = settings.OLLAMA_PRIMARY_MODEL
OLLAMA_FALLBACK_MODELS = settings.fallback_models_list

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY

PRIMARY_COLOR = settings.PRIMARY_COLOR
SECONDARY_COLOR = settings.SECONDARY_COLOR
CORS_ORIGINS = settings.CORS_ORIGINS
