import re
from typing import List, Dict
def _split_paragraphs(text: str) -> List[str]:
    # split on blank lines, keep non-empty
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[Dict]:
    """
    Greedy paragraph packing into ~chunk_size characters.
    If a single paragraph is longer than chunk_size, hard-split with overlap.
    Returns: [{"chunk_index": i, "text": "..."}]
    """
    if not text:
        return [{"chunk_index": 0, "text": ""}]
    paras = _split_paragraphs(text)
    chunks: List[str] = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) + (2 if buf else 0) <= chunk_size:
            buf = f"{buf}\n\n{p}" if buf else p
        else:
            if buf:
                chunks.append(buf)
            # long paragraph → hard split
            if len(p) > chunk_size:
                step = max(1, chunk_size - overlap)
                for i in range(0, len(p), step):
                    chunks.append(p[i:i + chunk_size])
                buf = ""
            else:
                buf = p
    if buf:
        chunks.append(buf)
    return [{"chunk_index": i, "text": c} for i, c in enumerate(chunks)]
