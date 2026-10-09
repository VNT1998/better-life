# Changelog

All notable changes to the BetterLife platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-10-09

### Added
- **Monorepo Architecture Modernization**:
  - Unified package management via `uv` (Python 3.12) with pinned lockfile (`uv.lock`).
  - Feature-sliced React 19 frontend with TypeScript `strict: true` and Vite.
  - TanStack Query v5 for server state caching and optimistic updates.
  - Root `Makefile` defining standardized development and verification targets.
  - Comprehensive GitHub Actions CI workflow covering backend and frontend quality gates.
- **Backend Architecture & Security**:
  - `pydantic-settings` runtime environment configuration in `app.core.config`.
  - RFC 7807 structured exception handling hierarchy (`AppException`, `NotFoundError`, `ValidationError`).
  - Structured JSON logging (`JSONFormatter`) and `RequestTracingMiddleware` with `X-Request-ID` and latency tracking.
  - Hardened bcrypt password hashing in `AuthService`.
  - Alembic database migration system with initial schema (`3c8dfe750fef_initial_schema.py`).
  - Production readiness (`/ready`) and health check (`/health`) probes.
  - Token-by-token Server-Sent Events (SSE) streaming endpoint (`POST /api/v1/chat/stream`).
- **Frontend Architecture & UX**:
  - Type-safe API client (`@/lib/api/client`) with normalized errors and request cancellation via `AbortController`.
  - Real-time token streaming chat view with live markdown rendering and sanitization (`rehype-sanitize`).
  - Comprehensive clinical workspace with patient records, document OCR viewer, longitudinal timeline, and guideline RAG explorer.
  - Top-level `ErrorBoundary` fallback and Vitest unit testing suites.
- **DevOps & Standards**:
  - Production multi-stage Dockerfiles for backend (non-root `appuser`) and frontend (unbuffered Nginx SSE proxy).
  - Pre-commit hygiene configuration (`.pre-commit-config.yaml`) and `.editorconfig`.
  - Dependabot automated weekly dependency scans.
  - System architecture guide (`docs/architecture.md`) and Architectural Decision Record (`docs/adr/0001-self-hosted-ollama-rag.md`).

### Changed
- Migrated all frontend JavaScript (`.js`/`.jsx`) code to strict TypeScript (`.ts`/`.tsx`).
- Replaced legacy `requirements.txt` with `backend/pyproject.toml` dependency groups.
- Standardized API endpoints under `/api/v1/*` while retaining `/api/*` aliases for backward compatibility.
- Cleaned up obsolete shim files and redundant dependencies.
