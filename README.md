# Business Knowledge Platform
FastAPI backend (Mongo + Chroma) with LLM chat and RAG (OpenAI → Ollama fallback).

## Features
- Auth (JWT)
- Document upload + text/metadata storage in Mongo
- Vector search over chunks (Chroma)
- Chat endpoint with **OpenAI primary and automatic fallback to local Ollama**
- Switchable routers (analytics/knowledge) via code or env flags

---

## Prerequisites
- **Python** 3.10+ (3.11 OK)
- **MongoDB** (local or cloud). Have a `MONGODB_URI`.
- **Ollama** (for local models) → https://ollama.com  
  - Install a model, e.g.:
    ```bash
    ollama pull llama3.2:3b
    ```
  - Start daemon (usually auto): `ollama serve`
- (Optional) **OpenAI** key if you want cloud models

---

## Quick Start (Windows PowerShell)
```powershell
# 1) clone and enter repo
git clone https://github.com/<you>/<repo>.git
cd .\<repo>

# 2) create venv + install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U -r requirements.txt  # if present
# if not present, install minimal deps:
# pip install -U fastapi "uvicorn[standard]" requests pydantic pymongo python-dotenv chromadb

# 3) copy env example and fill values
Copy-Item .env.example .env
# edit .env and set at least: MONGODB_URI, JWT_SECRET
# for local LLM: LLM_PRIMARY=ollama, OLLAMA_URL=http://127.0.0.1:11434, LLM_MODEL=llama3.2:3b

# 4) (recommended for older Ollama) force generate endpoint
$env:OLLAMA_USE_GENERATE = "1"

# 5) run the API (port 8010 by default below)
python -m uvicorn app.main:app --reload --port 8010
