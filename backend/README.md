# Blood Report Analyzer - Backend

FastAPI backend providing blood report analysis, PDF text extraction, and follow-up medical Q&A powered by self-hosted Ollama (`https://ollama.calmalpha.in/`) and Supabase Authentication.

## Running

```bash
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload --port 8000
```
