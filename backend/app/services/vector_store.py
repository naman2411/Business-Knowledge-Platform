from typing import List, Dict, Optional
import re, math, zlib
from chromadb import HttpClient
from app.core.config import settings
_client = HttpClient(host=settings.chroma_host, port=settings.chroma_port)
EMBED_DIM = 384  # keep whatever you already use
_collection = _client.get_or_create_collection(f"bkp_chunks_{EMBED_DIM}")
def _hash_embed_batch(texts: List[str], dim: int) -> List[List[float]]:
    out = []
    for t in texts:
        v = [0.0]*dim
        for tok in re.findall(r"[A-Za-z0-9]+", (t or "").lower()):
            h = zlib.adler32(tok.encode("utf-8")) % dim
            v[h] += 1.0
        n = math.sqrt(sum(x*x for x in v)) or 1.0
        out.append([x/n for x in v])
    return out
def _embed_batch(texts: List[str]) -> List[List[float]]:
    return _hash_embed_batch(texts, EMBED_DIM)  # keep your real providers if you have them
def add_documents(ids, documents, metadatas):
    embeddings = _embed_batch(documents)
    _collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
def similarity_search(query: str, top_k: int = 5, document_id: Optional[str] = None):
    qvec = _embed_batch([query])[0]
    where = {"document_id": document_id} if document_id else None
    res = _collection.query(query_embeddings=[qvec], n_results=top_k, where=where)
    hits: List[Dict] = []
    if res.get("ids"):
        for i in range(len(res["ids"][0])):
            hits.append({
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
            })
    return hits
def get_chunks_by_document(document_id: str, limit: int = 100):
    """Return all chunks for a single document_id (no retrieval, just fetch)."""
    res = _collection.get(
        where={"document_id": document_id},
        limit=limit,
        include=["ids","documents","metadatas"]
    )
    hits = []
    ids = res.get("ids") or []
    docs = res.get("documents") or []
    metas = res.get("metadatas") or []
    for i in range(len(ids)):
        hits.append({"id": ids[i], "text": docs[i], "metadata": metas[i]})
    return hits
