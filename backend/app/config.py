import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Blood Report Analyzer"
APP_DESCRIPTION = "Comprehensive AI-Powered Blood Report and Laboratory Health Insights"
APP_ICON = "🩺"
APP_TAGLINE = "Discover a Healthier You with AI"

# App settings
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "50"))
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
ANALYSIS_DAILY_LIMIT = int(os.getenv("ANALYSIS_DAILY_LIMIT", "15"))

# Ollama Settings (Self-hosted model endpoint)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.calmalpha.in").rstrip("/")
OLLAMA_PRIMARY_MODEL = os.getenv("OLLAMA_PRIMARY_MODEL", "gemma4:e4b")
OLLAMA_FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("OLLAMA_FALLBACK_MODELS", "phi4-mini:latest,granite4.1:3b,qwen3.5:4b-mlx").split(",")
    if m.strip()
]

# Supabase Auth & Database Settings
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))

# UI Settings
PRIMARY_COLOR = "#0ea5e9"
SECONDARY_COLOR = "#0284c7"
