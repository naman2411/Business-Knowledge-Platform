@'
# Business Knowledge Platform
FastAPI backend (Mongo + Chroma-ready) with LLM chat (OpenAI → Ollama fallback).

## Enabled Routers (per `app/main.py`)
- **/api/auth/** — register, login (JWT)
- **/api/documents/** — upload & list documents
- **/api/knowledge/** — for getting summary of the documents
- **/api/** — health/status


---

## Prerequisites
- **Python** 3.10+ (3.11 OK)
- **MongoDB** connection URI (local or Atlas): `MONGODB_URI`
- **Ollama** for local models (https://ollama.com)  
  - Example: `ollama pull llama3.2:3b`  
  - Daemon (usually auto): `ollama serve`
- *(Optional)* **OpenAI** key if you want cloud models

---

## Quick Start (Windows PowerShell)
```powershell
# 1) clone and enter repo
git clone https://github.com/<you>/<repo>.git
cd .\<repo>

# 2) create venv + install deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U -r requirements.txt  # if present
# If you don't have requirements.txt yet:
# pip install -U fastapi "uvicorn[standard]" requests pydantic pymongo python-dotenv

# 3) copy env example and fill values
Copy-Item .env.example .env
# Set at least:
# MONGODB_URI=mongodb://localhost:27017/<db>
# JWT_SECRET=change_me
# ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
# For local LLM:
# LLM_PRIMARY=ollama
# OLLAMA_URL=http://127.0.0.1:11434
# LLM_MODEL=llama3.2:3b

# 4) (recommended for older Ollama) use /api/generate
$env:OLLAMA_USE_GENERATE = "1"

# 5) run the API (port 8010)
python -m uvicorn app.main:app --reload --port 8010
