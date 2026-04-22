from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.core.exceptions import FileExtractionError


def extract_text_from_upload(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    try:
        if suffix in {".txt", ".md"}:
            return content.decode("utf-8")
        if suffix == ".pdf":
            reader = PdfReader(BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        if suffix == ".docx":
            document = Document(BytesIO(content))
            return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    except Exception as exc:  # pragma: no cover - defensive wrapper
        raise FileExtractionError(f"Failed to extract text from {filename}") from exc

    raise FileExtractionError(f"Unsupported file type: {suffix}")
