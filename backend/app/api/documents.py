import os
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from bson import ObjectId, regex
from app.core.config import settings
from app.core.db import get_db
from app.ingestion.parsers import extract_text
from app.ingestion.chunk import chunk_text
from app.services.vector_store import add_documents
router = APIRouter()
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if file.size and file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    os.makedirs(settings.file_storage_dir, exist_ok=True)
    storage_path = os.path.join(settings.file_storage_dir, file.filename)
    with open(storage_path, "wb") as f:
        f.write(await file.read())
    text = await extract_text(storage_path, file.content_type or "")
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text extracted")
    chunks = chunk_text(text)
    db = get_db()
    ext = os.path.splitext(file.filename)[1].lstrip(".").lower()
    doc = {
        "filename": file.filename,
        "ext": ext,
        "content_type": file.content_type,
        "size": file.size,
        "storage_path": storage_path,
        "uploaded_at": datetime.utcnow(),
        "chunk_count": len(chunks),
    }
    res = await db.documents.insert_one(doc)
    doc_id = str(res.inserted_id)
    ids = [f"{doc_id}:{i}" for i in range(len(chunks))]
    metadatas = [{"document_id": doc_id, "chunk_index": i, "filename": file.filename} for i in range(len(chunks))]
    docs = [c["text"] for c in chunks]
    add_documents(ids, docs, metadatas)
    return {"document_id": doc_id, "chunks": len(chunks)}
@router.get("")
async def list_documents(
    search: str | None = Query(None, description="Case-insensitive search in filename"),
    ext: str | None = Query(None, description="Filter by extension: pdf|docx|txt|md"),
    date_from: str | None = Query(None, description="ISO date e.g. 2025-08-01"),
    date_to: str | None = Query(None, description="ISO date e.g. 2025-08-12"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    db = get_db()
    q: Dict[str, Any] = {}
    if search:
        q["filename"] = {"$regex": search, "$options": "i"}
    if ext:
        q["ext"] = ext.lower()
    if date_from or date_to:
        rng = {}
        from datetime import datetime
        if date_from:
            try: rng["$gte"] = datetime.fromisoformat(date_from)
            except: pass
        if date_to:
            try: rng["$lte"] = datetime.fromisoformat(date_to)
            except: pass
        if rng: q["uploaded_at"] = rng
    cursor = db.documents.find(q).sort("uploaded_at", -1).skip((page-1)*size).limit(size)
    out: List[Dict[str, Any]] = []
    async for d in cursor:
        out.append({
            "id": str(d["_id"]),
            "filename": d.get("filename"),
            "ext": d.get("ext"),
            "content_type": d.get("content_type"),
            "size": d.get("size"),
            "uploaded_at": d.get("uploaded_at").isoformat() if d.get("uploaded_at") else None,
            "chunk_count": d.get("chunk_count"),
        })
    total = await db.documents.count_documents(q)
    return {"page": page, "size": size, "total": total, "items": out}
