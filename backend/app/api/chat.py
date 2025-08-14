from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import os
from app.services.llm_providers import OpenAIProvider, OllamaProvider
router = APIRouter()
PRIMARY = os.getenv("LLM_PRIMARY", "openai")  # "openai" or "ollama"
class ChatIn(BaseModel):
    prompt: str
    system: str | None = None
    model: str | None = None
def sse(event: str, data: str):
    return f"event: {event}\ndata: {data}\n\n".encode("utf-8")
@router.post("/chat/stream")
def chat_stream(body: ChatIn):
    prompt, system = body.prompt, body.system
    def gen():
        yield sse("typing", "start")
        # Try OpenAI first if configured
        if PRIMARY == "openai" and os.getenv("OPENAI_API_KEY"):
            try:
                oa = OpenAIProvider(model=os.getenv("OPENAI_MODEL") or body.model)
                text = oa.complete(prompt, system=system)  # non-stream call
                if text:
                    yield sse("token", text)
                    yield sse("done", "end")
                    return
            except Exception as e:
                msg = str(e)
                is_429 = ("429" in msg) or ("insufficient_quota" in msg)
                if not is_429:
                    yield sse("error", "openai_failed")
                    yield sse("done", "end")
                    return
                # else: fall through to Ollama
        # Ollama (primary or fallback)
        try:
            ol = OllamaProvider(model=os.getenv("LLM_MODEL") or body.model)
            for delta in ol.stream(prompt, system=system):
                yield sse("token", delta)
            yield sse("done", "end")
        except Exception:
            yield sse("error", "ollama_failed")
            yield sse("done", "end")
    return StreamingResponse(gen(), media_type="text/event-stream")
@router.post("/chat/complete")
def chat_complete(body: ChatIn):
    prompt, system = body.prompt, body.system
    if PRIMARY == "openai" and os.getenv("OPENAI_API_KEY"):
        try:
            oa = OpenAIProvider(model=os.getenv("OPENAI_MODEL") or body.model)
            return JSONResponse({"reply": oa.complete(prompt, system=system)})
        except Exception as e:
            msg = str(e)
            is_429 = ("429" in msg) or ("insufficient_quota" in msg)
            if not is_429:
                return JSONResponse({"error": "openai_failed"}, status_code=500)
            # else fall back
    try:
        ol = OllamaProvider(model=os.getenv("LLM_MODEL") or body.model)
        return JSONResponse({"reply": ol.complete(prompt, system=system)})
    except Exception:
        return JSONResponse({"error": "ollama_failed"}, status_code=500)
