import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.auth import router as auth_router
from api.sessions import router as sessions_router
from api.analysis import router as analysis_router
from api.chat import router as chat_router
from api.models import router as models_router
from config.app_config import APP_NAME, APP_TAGLINE, APP_DESCRIPTION

app = FastAPI(
    title=f"{APP_NAME} - {APP_TAGLINE}",
    description=APP_DESCRIPTION,
    version="2.0.0",
)

# CORS configuration to allow React frontend (Vite dev on 5173 or any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(models_router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": "2.0.0",
    }


# Serve built React frontend if frontend/dist exists
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/") or full_path == "api":
            return {"error": "API route not found"}
        target_file = frontend_dist / full_path
        if target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    def index():
        return {
            "message": f"Welcome to {APP_NAME} API. React frontend dev server runs on http://localhost:5173",
            "docs": "/docs",
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
