import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.analysis import router as analysis_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.clinical_analyses import router as analyses_router
from app.api.clinical_audit import router as audit_router
from app.api.clinical_documents import router as documents_router
from app.api.clinical_knowledge_bases import router as kb_router
from app.api.clinical_patients import router as patients_router
from app.api.models import router as models_router
from app.api.sessions import router as sessions_router
from app.core.config import settings
from app.core.errors import AppException, app_exception_handler, generic_exception_handler
from app.core.logging import setup_logging
from app.core.middleware import RequestTracingMiddleware
from app.db.init_db import init_db
from app.db.session import engine

# Configure structured production logging
setup_logging(debug=settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database schema & seed clinical guidelines
    init_db()
    yield
    # Shutdown logic (clean up connections if needed)


app = FastAPI(
    title=f"{settings.APP_NAME} - {settings.APP_TAGLINE}",
    description=settings.APP_DESCRIPTION,
    version="2.0.0",
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Tracing & Telemetry Middleware (adds X-Request-ID, X-Response-Time)
app.add_middleware(RequestTracingMiddleware)

# Strict CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)

# API routers list
ROUTERS = [
    auth_router,
    sessions_router,
    analysis_router,
    chat_router,
    models_router,
    documents_router,
    patients_router,
    kb_router,
    analyses_router,
    audit_router,
]

# Mount versioned routes (/api/v1) as primary API contract
for r in ROUTERS:
    app.include_router(r, prefix="/api/v1")

# Mount legacy routes (/api) for backwards compatibility
for r in ROUTERS:
    app.include_router(r, prefix="/api")


@app.get("/health", tags=["system"])
@app.get("/api/health", tags=["system"])
@app.get("/api/v1/health", tags=["system"])
def health_check():
    """Liveness probe: verifies service process is running."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready", tags=["system"])
@app.get("/api/ready", tags=["system"])
@app.get("/api/v1/ready", tags=["system"])
def readiness_check():
    """Readiness probe: verifies database connectivity and core subsystems."""
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "unavailable"},
        )

    return {
        "status": "ready",
        "database": "connected",
        "service": settings.APP_NAME,
        "version": "2.0.0",
    }


# Serve built React frontend if frontend/dist exists
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if (
            full_path.startswith("api/")
            or full_path.startswith("health")
            or full_path.startswith("ready")
        ):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "Endpoint not found"},
            )
        target_file = frontend_dist / full_path
        if target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(frontend_dist / "index.html")
else:

    @app.get("/")
    def index():
        return {
            "message": f"Welcome to {settings.APP_NAME} API. React frontend dev server runs on http://localhost:5173",
            "docs": "/docs",
            "version": "2.0.0",
        }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
