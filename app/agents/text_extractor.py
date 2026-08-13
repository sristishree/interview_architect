"""
Text Extractor
--------------
Pure text extraction from a resume file — no LLM involved.

Strategy:
  PDF (text-based)  — pypdf (fast, no dependencies)
  PDF (scanned)     — PaddleOCR via PyMuPDF page rendering (lazy-imported)
  DOCX              — python-docx
  TXT               — plain read

A PDF is considered scanned when pypdf returns fewer than MIN_TEXT_CHARS characters
of non-whitespace content. PaddleOCR is only imported/initialised when actually needed.
"""

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.graph.state import InterviewState

logger = logging.getLogger(__name__)

MIN_TEXT_CHARS = 100


def _read_pdf_text(path: str) -> str:
    import pypdf
    with open(path, "rb") as f:
        reader = pypdf.PdfReader(f)
        return "\n".join(page.extract_text() or "" for page in reader.pages)


def _ocr_pdf(path: str) -> str:
    """Render each PDF page to a numpy image and run PaddleOCR on it."""
    import fitz  # pymupdf
    import numpy as np
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    doc = fitz.open(path)
    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        result = ocr.ocr(img, cls=True)
        page_text = "\n".join(
            line[1][0]
            for block in (result or [])
            for line in (block or [])
        )
        pages.append(page_text)
    return "\n\n".join(pages)


def _read_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        text = _read_pdf_text(path)
        if len(text.replace(" ", "").replace("\n", "")) < MIN_TEXT_CHARS:
            logger.info("pypdf returned sparse text for %s — falling back to PaddleOCR", path)
            text = _ocr_pdf(path)
        return text

    if ext == ".docx":
        import docx
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text_node(state: "InterviewState") -> dict:
    raw_text = _read_file(state["resume_path"])
    return {"raw_text": raw_text}
