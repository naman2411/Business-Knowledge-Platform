# Business Knowledge Platform — Mongo + Chroma Starter
## Quickstart
1) Copy env:
   - PowerShell: `copy .env.example .env`
2) Start:
   - `docker compose up --build`
3) Open:
   - API docs: http://localhost:8000/docs
4) Test:
   - POST `/api/documents/upload` with a PDF/TXT
   - POST `/api/knowledge/ask` with {"query":"..."}
If OPENAI_API_KEY is set in `.env`, answers use the LLM; else demo mode.
