# 🌱 BetterLife

[![CI Quality Gate](https://github.com/vinitkarkera/better-life/actions/workflows/ci.yml/badge.svg)](https://github.com/vinitkarkera/better-life/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![React 19](https://img.shields.io/badge/react-19-61dafb.svg)](https://react.dev/)
[![TypeScript Strict](https://img.shields.io/badge/typescript-strict-3178c6.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Production-grade Clinical Evidence Intelligence and Laboratory Blood Report Analysis Platform with interactive clinical follow-up Q&A, built with **React 19 + TypeScript (Vite)**, **FastAPI (Python 3.12 + uv)**, and self-hosted **Ollama** model inference.

---

## 🌟 Key Features

- **Clinical Evidence Intelligence Engine (CEI)**:
  - **Multimodal Ingestion**: PDF, image, and text ingestion with page segmentation, OCR fallback, and token-level provenance.
  - **Structured Pydantic Extraction**: Extracts patient vitals, dates, lab observations, units, reference intervals, flags, and interpretations into typed schemas.
  - **Longitudinal Biomarker Modeling**: Longitudinal trajectory tracking (`RISING`, `FALLING`, `STABLE`, `NEW`, `MISSING`) across historical patient visits with absolute and percentage shifts.
  - **Evidence-Grounded Clinical RAG**: Vector-indexed authoritative standards from ADA, AHA/ACC, KDIGO, WHO, and ASH.
  - **Deterministic Safety Guardrail**: Programmatic application-level filter blocking prescription generation, drug dosing, and definitive diagnosis claims before responses reach clients.
  - **Real-Time Token Streaming**: Server-Sent Events (SSE) token-by-token streaming with immediate cancellation via `AbortController`.
  - **Reference AI Workload**: Production adapter for **Nuvorix**.
- **Automated Clinical Evaluation Harness**:
  - Synthetic golden benchmark dataset measuring extraction precision/recall ($\ge 85\%$), longitudinal trend accuracy ($100\%$), and safety violation detection ($100\%$).
- **Zero-Cloud AI Dependency**:
  - Completely private inference via self-hosted Ollama (`https://ollama.calmalpha.in/`).
  - Hierarchical model fallback cascade (`gemma4:e4b` $\to$ `phi4-mini` $\to$ `granite4.1:3b` $\to$ `qwen3.5:4b-mlx`).
- **Production Monorepo Engineering**:
  - Backend dependency locking with Astral [`uv`](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`).
  - Strict TypeScript configuration (`strict: true`) and ESLint flat config + Prettier formatting.
  - Layered backend architecture, RFC 7807 structured error responses, and `X-Request-ID` telemetry middleware.
  - Automated database migrations via Alembic (`backend/alembic/`).
  - Hardened multi-stage Dockerfiles with non-root security users and unbuffered Nginx reverse proxies.

---

## 🛠️ Architecture & Tech Stack

```
.
├── backend/                  # FastAPI Application (Python 3.12, uv)
│   ├── app/
│   │   ├── api/              # Thin HTTP controllers (/api/v1 and /api)
│   │   ├── core/             # pydantic-settings, errors, logging, telemetry
│   │   ├── services/         # Orchestrator, safety, timeline, knowledge base
│   │   ├── agents/           # Ollama client, extraction agent, chat agent
│   │   ├── schemas/          # Clinical Pydantic schemas
│   │   ├── db/               # SQLAlchemy models & Alembic migrations
│   │   └── main.py           # Application entrypoint
│   ├── tests/                # Unit (unit/) and Integration (integration/) tests
│   ├── pyproject.toml        # Single source of truth for dependencies
│   └── uv.lock               # Deterministic dependency lockfile
├── frontend/                 # React 19 + TypeScript SPA (Vite)
│   ├── src/
│   │   ├── app/              # Shell, ErrorBoundary, TanStack Query providers
│   │   ├── features/         # Feature-sliced domains (clinical, chat, auth, sessions)
│   │   ├── components/       # Shared reusable UI
│   │   ├── lib/              # Typed API client, Zod env validation
│   │   └── test/             # Vitest & React Testing Library test suites
│   ├── vite.config.ts        # Vite config with @/ path alias
│   └── package.json
├── docs/                     # Architecture guide & Architectural Decision Records
├── .github/                  # CI workflow, Dependabot, PR & issue templates
├── Makefile                  # Standardized build and quality gate targets
└── docker-compose.yml        # PostgreSQL (pgvector), Redis, Backend, Frontend
```

For detailed system design diagrams and rationale, see [Architecture Documentation](docs/architecture.md) and [ADR 0001: Self-Hosted Ollama](docs/adr/0001-self-hosted-ollama-rag.md).

---

## 🚀 Quickstart & Development

### 1. Prerequisites
- [Python 3.12+](https://www.python.org/)
- [`uv`](https://docs.astral.sh/uv/) (Astral Python package manager)
- [Node.js 20+](https://nodejs.org/) and `npm`
- [Docker](https://www.docker.com/) (Optional, for PostgreSQL + pgvector)

### 2. Installation
Install all backend and frontend dependencies with one command:
```bash
make install
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Key environment settings:
```env
ENVIRONMENT=development
SECRET_KEY=your-secure-random-secret-key-at-least-16-chars
OLLAMA_BASE_URL=https://ollama.calmalpha.in/
OLLAMA_PRIMARY_MODEL=gemma4:e4b
OLLAMA_FALLBACK_MODELS=phi4-mini:latest,granite4.1:3b,qwen3.5:4b-mlx
DATABASE_URL=sqlite:///./betterlife_platform.db
```

### 4. Running Locally
Run the backend and frontend in separate terminals:

```bash
# Terminal 1: Backend API (http://localhost:8000)
make dev-backend

# Terminal 2: Frontend Web App (http://localhost:5173)
make dev-frontend
```

Interactive OpenAPI Swagger documentation is available at:
`http://localhost:8000/docs`

---

## 🧪 Quality Gates & Verification

Run the full quality gate verifying linting, formatting, static typing, unit/integration tests, and production builds:

```bash
make check
```

Individual target commands:
| Command | Description |
| ------- | ----------- |
| `make lint` | Run Ruff on backend and ESLint on frontend |
| `make format` | Automatically format code with Ruff and Prettier |
| `make format-check` | Verify formatting without modifying files |
| `make typecheck` | Run Mypy (strict) on backend and `tsc --noEmit` on frontend |
| `make test` | Run Pytest with coverage on backend and Vitest on frontend |
| `make build` | Compile optimized production frontend bundle |
| `make audit` | Scan for package vulnerabilities (`pip-audit` & `npm audit`) |

---

## 🐳 Docker Deployment

To launch the full production composition (PostgreSQL with `pgvector`, Redis, FastAPI backend, and Nginx React frontend):

```bash
docker compose up --build -d
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Readiness Probe**: http://localhost:8000/ready

---

## 🔒 Security & Governance

- See [SECURITY.md](SECURITY.md) for our security posture and vulnerability disclosure instructions.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
