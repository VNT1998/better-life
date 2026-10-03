# 🩺 HIA (Health Insights Agent)

AI Agent to analyze blood reports and provide detailed health insights, built with **React (Vite)**, **FastAPI (uv)**, and self-hosted **Ollama**.

<p align="center">
  <img src="public/HIA_demo.gif" alt="HIA Demo" width="700" />
</p>

## 🌟 Key Highlights & Features

- **Self-Hosted AI Models (Zero External Model APIs)**:
  - Direct inference using your self-hosted Ollama server (`https://ollama.calmalpha.in/`).
  - Supported models: `gemma4:e4b`, `phi4-mini:latest`, `granite4.1:3b`, `qwen3.5:4b-mlx`.
  - Multi-model automatic fallback cascade.
- **Modern React Frontend (Vite + Tailwind CSS)**:
  - Fast, responsive user interface with drag-and-drop PDF upload or instant sample blood report testing.
  - Interactive diagnosis dashboard with markdown formatting, risks, and recommendations.
  - Interactive follow-up Q&A chat powered by Ollama.
- **FastAPI Backend (managed with `uv`)**:
  - Blazingly fast asynchronous API endpoints for authentication, sessions, PDF extraction, analysis, and chat.
- **Authentication & Persistence (Supabase)**:
  - User sign up, sign in, token authentication, and session persistence in Supabase PostgreSQL tables.
  - Automatic local in-memory fallback for rapid local development without mandatory cloud configuration.
- **PDF Extraction & Validation**:
  - Text extraction via `pdfplumber` with medical content validation and size limits (max 20MB, max 50 pages).
- **Daily Analysis Limit**:
  - Configurable daily limit (default 15/day) with progress indicators.

---

## 🛠️ Tech Stack

- **Frontend**: React 19, Vite, Tailwind CSS v4, Lucide React, React Markdown
- **Backend**: FastAPI, Uvicorn, Python 3.12+ (managed with `uv`)
- **AI / LLM**: Self-hosted Ollama (`https://ollama.calmalpha.in/`)
- **Database / Auth**: Supabase (PostgreSQL) / Gotrue with local fallback
- **PDF Engine**: PDFPlumber, filetype

---

## 🚀 Quick Start Guide

### 1. Requirements

- Python 3.10+ and [`uv`](https://github.com/astral-sh/uv)
- Node.js 18+ and `npm`

### 2. Environment Setup

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your `.env` settings:
```env
OLLAMA_BASE_URL=https://ollama.calmalpha.in/
OLLAMA_PRIMARY_MODEL=gemma4:e4b
OLLAMA_FALLBACK_MODELS=phi4-mini:latest,granite4.1:3b,qwen3.5:4b-mlx

# Supabase Auth & Database (optional, falls back to local storage if omitted)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

### 3. Install Dependencies

**Python Backend** (using `uv`):
```bash
uv venv
uv pip install -r requirements.txt
```

**React Frontend** (using `npm`):
```bash
cd frontend
npm install
cd ..
```

### 4. Running the Application

**Option A: Development Mode (with hot-reloading)**

1. Start the FastAPI backend:
```bash
npm run dev:backend
# or: PYTHONPATH=src uv run uvicorn main:app --reload --port 8000
```

2. Start the Vite React frontend:
```bash
npm run dev:frontend
# or: cd frontend && npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

**Option B: Full-Stack Production Mode**

Build the frontend and serve everything directly from FastAPI:
```bash
npm run build
npm run start
```
Visit **`http://localhost:8000`** in your browser.

---

## 📁 Project Structure

```
blood-report-analysis/
├── frontend/                   # React + Vite Frontend
│   ├── src/
│   │   ├── api/client.js       # Backend API client
│   │   ├── context/AuthContext.jsx # Authentication state
│   │   ├── components/
│   │   │   ├── Navbar.jsx      # Navigation, model selector, user status
│   │   │   ├── Sidebar.jsx     # Session history, new session, limits
│   │   │   ├── AnalysisForm.jsx # PDF upload / sample report form
│   │   │   ├── ChatView.jsx    # Chat thread, report analysis, follow-up Q&A
│   │   │   ├── WelcomeView.jsx # Welcome hero screen
│   │   │   └── AuthModal.jsx   # Login & register modal
│   │   ├── App.jsx             # Main React application
│   │   └── index.css           # Tailwind CSS styles
│   └── vite.config.js          # Vite config with API proxy
├── src/                        # FastAPI Backend
│   ├── api/                    # API Routers
│   │   ├── auth.py             # User signup, login, session validation
│   │   ├── sessions.py         # Chat sessions CRUD
│   │   ├── analysis.py         # PDF extraction & blood report analysis
│   │   ├── chat.py             # Follow-up RAG Q&A
│   │   └── models.py           # Ollama model discovery and app config
│   ├── agents/
│   │   ├── model_manager.py    # Ollama inference & fallback manager
│   │   ├── analysis_agent.py   # Medical analysis & in-context learning
│   │   └── chat_agent.py       # Follow-up Q&A agent
│   ├── auth/
│   │   └── auth_service.py     # Supabase auth & local in-memory fallback
│   ├── services/
│   │   └── ai_service.py       # High-level AI service layer
│   ├── utils/
│   │   ├── pdf_extractor.py    # PDF text extraction
│   │   └── validators.py       # Content and input validators
│   ├── config/
│   │   ├── app_config.py       # Settings & environment variables
│   │   ├── prompts.py          # Specialist medical prompts
│   │   └── sample_data.py      # Preloaded sample report
│   └── main.py                 # FastAPI app entrypoint
├── requirements.txt            # Python dependencies (managed via uv)
├── package.json                # Root helper scripts
└── README.md
```

## 🔒 Database Setup (Supabase)

If using Supabase, execute `public/db/script.sql` in your Supabase SQL Editor to create the required tables (`users`, `chat_sessions`, and `chat_messages`).
