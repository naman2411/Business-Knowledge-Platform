from fastapi import APIRouter, HTTPException, Query
from starlette.responses import StreamingResponse
from typing import AsyncGenerator
from app.services.vector_store import similarity_search
from app.services.llm import stream_answer
router = APIRouter()
@router.get("/chat/stream")
async def chat_stream(
    document_id: str = Query(...),
    q: str = Query(..., min_length=1)
):
    hits = similarity_search(q, top_k=8, document_id=document_id)
    if not hits:
        raise HTTPException(status_code=404, detail="No context for this document")
    async def event_gen() -> AsyncGenerator[bytes, None]:
        # typing indicator
        yield b"event: typing\ndata: start\n\n"
        async for chunk in stream_answer(q, hits):
            if chunk:
                # token event
                data = chunk.replace("\r", "")
                yield f"event: token\ndata: {data}\n\n".encode("utf-8")
        yield b"event: done\ndata: end\n\n"
    return StreamingResponse(event_gen(), media_type="text/event-stream")
