from typing import List, Dict, Tuple, AsyncGenerator
from app.core.config import settings
import asyncio

def _format_context(hits: List[Dict]) -> str:
    return "\n\n".join([(h.get("text") or "")[:1000] for h in hits if h.get("text")])
def _used_sources(hits: List[Dict]) -> List[Dict]:
    out = []
    for h in hits:
        md = h.get("metadata") or {}
        out.append({
            "id": h.get("id"),
            "filename": md.get("filename"),
            "chunk_index": md.get("chunk_index"),
        })
    return out
def answer_with_context(query: str, hits: List[Dict]) -> Tuple[str, List[Dict]]:
    """
    Non-streaming answer. Uses OpenAI if OPENAI_API_KEY present; otherwise returns a simple fallback.
    """
    context = _format_context(hits)
    used = _used_sources(hits)
    openai_key = getattr(settings, "openai_api_key", None)
   
    if not openai_key:
        answer = (
            "Summary (fallback): "
            + (query or "").strip()
            + "\n\nContext preview:\n"
            + (context[:400] if context else "(no context)")
        )
        return answer, used
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        prompt = (
            "Return PLAIN TEXT only (no markdown). "
            "Use simple sections if helpful:\n"
            "Summary:\nResources:\nTopics:\nPeople:\nActions:\nOne-line takeaway:\n"
            "Use '- ' for bullets. No emojis.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        ans = resp.choices[0].message.content or ""
        return ans, used
    except Exception as e:
        
        return f"(LLM error; fallback text) {e}\n\n{context[:500]}", used
async def stream_answer(query: str, hits: List[Dict]) -> AsyncGenerator[str, None]:
    """
    Streaming answer as an async generator of small text chunks.
    Tries OpenAI streaming if key is set; if not, tries Ollama if configured; else falls back.
    """
    context = _format_context(hits)
    openai_key = getattr(settings, "openai_api_key", None)
   
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": (
                        "Return PLAIN TEXT only (no markdown). "
                        "Use simple section labels if helpful:\n"
                        "Summary:\nResources:\nTopics:\nPeople:\nActions:\nOne-line takeaway:\n"
                        "Use '- ' for bullets. No emojis.\n\n"
                        f"Context:\n{context}\n\nQuestion: {query}"
                    )
                }],
                temperature=0.2,
                stream=True,
            )
            for chunk in stream:
                piece = ""
                try:
                    piece = chunk.choices[0].delta.content or ""
                except Exception:
                    piece = ""
                if piece:
                    yield piece
            return
        except Exception:
            pass 
    
    provider = str(getattr(settings, "llm_provider", "openai")).lower()
    if provider == "ollama":
        import json, requests
        base = getattr(settings, "ollama_base_url", "http://127.0.0.1:11434")
        model = getattr(settings, "ollama_model", "llama3.1")
        try:
            url = f"{base}/api/chat"
            payload = {
                "model": model,
                "stream": True,
                "messages": [
                    {"role": "system", "content":
                        "Return PLAIN TEXT only. Avoid markdown symbols. Use simple bullets '- ' if needed."
                    },
                    {"role": "user", "content":
                        f"CONTEXT:\n{context}\n\nTASK: {query}"
                    }
                ]
            }
            with requests.post(url, json=payload, stream=True, timeout=300) as r:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        await asyncio.sleep(0)
                        continue
                    
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    msg = (obj.get("message") or {}).get("content") or obj.get("response") or ""
                    if msg:
                        yield msg
            return
        except Exception:
            pass 
   
    ans, _ = answer_with_context(query, hits)
    for i in range(0, len(ans), 64):
        yield ans[i:i+64]
        await asyncio.sleep(0)

import os
from app.services.llm_providers import OpenAIProvider, OllamaProvider
def complete_with_fallback(prompt: str, system: str | None = None, model: str | None = None) -> str:
    """
    Try OpenAI first (if key present) and cleanly fall back to Ollama on 429 (insufficient_quota)
    or when OPENAI_API_KEY is absent. Never returns provider error text.
    """
    use_openai = os.getenv("LLM_PRIMARY", "openai") == "openai" and os.getenv("OPENAI_API_KEY")
    if use_openai:
        try:
            return OpenAIProvider(model=os.getenv("OPENAI_MODEL") or model or "o4-mini").complete(prompt, system=system)
        except Exception as e:
            msg = str(e)
            is_quota = ("429" in msg) or ("insufficient_quota" in msg)
            if not is_quota:
                
                raise
           
    return OllamaProvider(model=os.getenv("LLM_MODEL") or model or "llama3.1:8b").complete(prompt, system=system)
