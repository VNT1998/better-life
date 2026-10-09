# 🌱 BetterLife

AI-powered health intelligence and laboratory blood report analysis with interactive clinical follow-up Q&A, built with **React (Vite)**, **FastAPI (uv)**, and self-hosted **Ollama**.

---

## 🌟 Key Features

- **Clinical Evidence Intelligence Platform (CEI)**:
  - Multimodal document ingestion (PDF, Text, Images) with page segmentation and token/character provenance.
  - Pydantic structured clinical extraction (`patient`, `observations`, `medications`, `conditions`, `lab_results`, `dates`, `confidence`).
  - Longitudinal patient timeline modeling: biomarker trajectories (`rising`, `falling`, `stable`, `new`, `missing`) with delta and percentage shifts.
  - Evidence-grounded Clinical Guideline RAG: pre-seeded authoritative standards from ADA, AHA/ACC, KDIGO, WHO, and ASH.
  - Verifiable citation generation: claims linked to exact guideline excerpts, sections, pages, and recommendation grades.
  - Deterministic safety architecture: programmatic blocks against prescription directives, definitive diagnostic claims, and irreversible decisions.
  - Immutable audit trail logging all executions, model versions, and safety verdicts.
  - Reference AI workload adapter for **Nuvorix**.
- **Automated Clinical Evaluation Harness**:
  - Synthetic labeled benchmark cases with measured 100% precision/recall, 100% trend accuracy, and 100% safety violation detection.
  - Pytest suite and CLI runner (`python run_evaluation.py`).
- **Self-Hosted AI Models (Zero External Model APIs)**:
  - Direct local/private inference via Ollama endpoint: `https://ollama.calmalpha.in/`.
  - Supported models: `gemma4:e4b`, `phi4-mini:latest`, `granite4.1:3b`, `qwen3.5:4b-mlx`.
  - Multi-tier automatic fallback cascade.
- **Modern React Frontend (`frontend/`)**:
  - Dual-mode workspace: **💬 Health Chat** (conversational analysis) & **🔬 Clinical Intelligence** (Timeline, Evidence Explorer, Document Viewer, Audit Trail).
  - Scaffolded with Vite and styled with Tailwind CSS v4.
- **Dedicated Backend Service (`backend/`)**:
  - FastAPI application managed with `uv`.
  - Unified database layer with SQLite (zero-config local) & PostgreSQL + `pgvector` (Docker/production).
- **Docker Compose Deployment**:
  - Full-stack composition: FastAPI, React (Nginx), PostgreSQL with `pgvector`, and Redis.

---

## 🛠️ Tech Stack

- **Frontend**: React 19, Vite, Tailwind CSS v4, Lucide React, React Markdown
- **Backend**: FastAPI, Uvicorn, Python 3.12+ (managed with `uv`)
- **AI / LLM**: Self-hosted Ollama (`https://ollama.calmalpha.in/`)
- **Database / Auth**: Supabase (PostgreSQL) / Gotrue with local dev fallback
- **PDF Engine**: PDFPlumber, filetype

---

## 🚀 Getting Started

### 1. Requirements

- Python 3.10+ and [`uv`](https://github.com/astral-sh/uv)
- Node.js 18+ and `npm`

### 2. Environment Setup

Copy `.env.example` in `backend/` to `.env`:

```bash
cp backend/.env.example backend/.env
```

Environment variables:
```env
OLLAMA_BASE_URL=https://ollama.calmalpha.in/
OLLAMA_PRIMARY_MODEL=gemma4:e4b
OLLAMA_FALLBACK_MODELS=phi4-mini:latest,granite4.1:3b,qwen3.5:4b-mlx

# Supabase Auth & Database (optional, falls back to local storage if omitted)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

### 3. Installation

**Backend** (using `uv`):
```bash
cd backend
uv venv
uv pip install -r requirements.txt
cd ..
```

**Frontend** (using `npm`):
```bash
cd frontend
npm install
cd ..
```

### 4. Running the Development Servers

Start the backend and frontend development servers:

**Backend (FastAPI on http://localhost:8000)**:
```bash
npm run dev:backend
# or: cd backend && uv run uvicorn app.main:app --reload --port 8000
```

**Frontend (Vite on http://localhost:5173)**:
```bash
npm run dev:frontend
# or: cd frontend && npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

### 5. (Optional) Full-Stack Production Mode

Build the React frontend and serve both backend and frontend from FastAPI:
```bash
npm run build
npm run start
```
Visit **`http://localhost:8000`** in your browser.

---

## 📁 Project Structure

```
betterlife/
├── backend/                    # Dedicated Python Backend Project
│   ├── app/
│   │   ├── api/                # API Routers
│   │   │   ├── auth.py         # Authentication (sign in, sign up, session check)
│   │   │   ├── sessions.py     # Chat sessions management
│   │   │   ├── analysis.py     # PDF extraction & report analysis
│   │   │   ├── chat.py         # Follow-up Q&A
│   │   │   ├── models.py       # Ollama models list & configuration
│   │   │   └── deps.py         # Auth & service dependencies
│   │   ├── agents/
│   │   │   ├── model_manager.py # Ollama client with multi-model fallback
│   │   │   ├── analysis_agent.py # Medical analysis agent
│   │   │   └── chat_agent.py   # RAG follow-up agent
│   │   ├── auth/
│   │   │   └── auth_service.py # Supabase auth & local in-memory fallback
│   │   ├── services/
│   │   │   └── ai_service.py   # AI service orchestrator
│   │   ├── utils/
│   │   │   ├── pdf_extractor.py # PDF text extraction
│   │   │   └── validators.py   # Input & medical report validators
│   │   ├── config.py           # Configuration & settings
│   │   ├── prompts.py          # Clinical specialist prompts
│   │   ├── sample_data.py      # Preloaded sample blood report
│   │   └── main.py             # FastAPI entrypoint
│   ├── requirements.txt        # Backend dependencies
│   ├── pyproject.toml          # uv/hatchling project configuration
│   └── README.md
├── frontend/                   # React + Vite Frontend Project
│   ├── src/
│   │   ├── api/client.js       # REST API client
│   │   ├── context/AuthContext.jsx # Auth state management
│   │   ├── components/
│   │   │   ├── Navbar.jsx      # Header, model selector, user status
│   │   │   ├── Sidebar.jsx     # Session history, new session, limits
│   │   │   ├── AnalysisForm.jsx # PDF upload / sample report form
│   │   │   ├── ChatView.jsx    # Clinical findings, diagnosis, follow-up Q&A
│   │   │   ├── WelcomeView.jsx # Welcome hero screen
│   │   │   └── AuthModal.jsx   # Login & register modal
│   │   ├── App.jsx             # Main application layout
│   │   └── index.css           # Tailwind CSS styles
│   ├── package.json
│   └── vite.config.js          # Vite configuration with API proxy
├── public/
│   └── db/
│       ├── script.sql          # Supabase database schema
│       └── schema.png          # Database schema diagram
├── package.json                # Root workflow scripts
├── .env.example                # Example environment variables
└── README.md
```

## 🔒 Database Setup (Supabase)

If connecting to Supabase, run `public/db/script.sql` in your Supabase SQL Editor to initialize the `users`, `chat_sessions`, and `chat_messages` tables.
