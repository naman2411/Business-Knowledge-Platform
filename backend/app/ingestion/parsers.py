from typing import Tuple
import os
from pypdf import PdfReader
from docx import Document
async def extract_text(path: str, content_type: str | None = "") -> str:
    # Decide by MIME or extension
    ext = os.path.splitext(path)[1].lower()
    ctype = (content_type or "").lower()
    try:
        if ext == ".pdf" or "pdf" in ctype:
            return _from_pdf(path)
        if ext == ".docx" or "wordprocessingml.document" in ctype:
            return _from_docx(path)
        if ext == ".md" or "markdown" in ctype:
            return _from_text(path)  # treat MD as plain text
        # default: TXT / unknown -> plain text
        return _from_text(path)
    except Exception as e:
        return f"[PARSE_ERROR] {e}"
def _from_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
def _from_docx(path: str) -> str:
    doc = Document(path)
    lines = []
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if t:
            lines.append(t)
    return "\n".join(lines)
def _from_pdf(path: str) -> str:
    # text-based PDFs; for scanned PDFs, add OCR later if needed
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        t = (page.extract_text() or "").strip()
        if t:
            parts.append(t)
    return "\n\n".join(parts).strip()
