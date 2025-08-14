from fastapi import APIRouter, HTTPException
from app.services.llm import complete_with_fallback
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Literal
import re
from app.services.vector_store import similarity_search, get_chunks_by_document
from app.services.llm import answer_with_context
router = APIRouter()
FormatType = Literal["plain", "one_line", "lines", "text"]
def _shape_answer(text: str, fmt: FormatType):
    if fmt == "one_line":
        return re.sub(r"\s*\n+\s*", " ", text).strip()
    if fmt == "lines":
        return [ln.strip() for ln in text.splitlines() if ln.strip()]
    # "plain" returns the raw string (with newlines) for JSON; "text" handled separately
    return text
class AskBody(BaseModel):
    query: str
    document_id: str
    format: FormatType | None = "plain"
@router.post("/knowledge/ask")
async def ask(body: AskBody):
    q = (body.query or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Empty query")
    raw_hits = similarity_search(q, top_k=12, document_id=body.document_id)
    seen, hits = set(), []
    for h in raw_hits:
        t = (h.get("text") or "").strip().lower()
        if not t or t in seen:
            continue
        seen.add(t)
        hits.append(h)
        if len(hits) >= 8:
            break
    # Build context from the retrieved chunks
    context = "\n\n".join(f"[{i+1}] {h.get('text','')}" for i, h in enumerate(hits))

    prompt = f"""Answer the question using ONLY the context. If the answer isn't in the context, say you don't know.

    CONTEXT:
    {context}

    QUESTION:
    {q}

    Answer:"""

    # Call the provider (OpenAI→Ollama fallback)
    ans = complete_with_fallback(
        prompt,
        system="You are a concise assistant. Answer using only the provided context."
    )

    # Shape sources from hits (keeps your old response shape)
    used = [
        {
            "id": h.get("id"),
            "filename": h.get("filename"),
            "chunk_index": h.get("chunk_index"),
        }
        for h in hits
    ]

    fmt = (body.format or "plain")
    if fmt == "text":
        # Return true newlines as text/plain
        return PlainTextResponse(ans)
    return {"answer": _shape_answer(ans, fmt), "sources": used}
class SummarizeBody(BaseModel):
    document_id: str
    style: str | None = None
    format: FormatType | None = "plain"
@router.post("/knowledge/summarize")
async def summarize(body: SummarizeBody):
    chunks = get_chunks_by_document(body.document_id, limit=100)
    if not chunks:
        raise HTTPException(status_code=404, detail="No chunks for document")
    query = body.style or "Summarize this document into clear sections and a one-line takeaway."
    ans, used = answer_with_context(query, chunks[:20])
    fmt = (body.format or "plain")
    if fmt == "text":
        return PlainTextResponse(ans)
    return {"answer": _shape_answer(ans, fmt), "sources": used}
