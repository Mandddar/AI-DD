"""
Text extraction from uploaded documents.
Supports: PDF, Word (.docx), Excel (.xlsx/.xls), plain text.
When GCP is available, swap extract_text() to call Google Document AI.
"""
import io
from pathlib import Path


def extract_text(file_bytes: bytes, mime_type: str, filename: str) -> tuple[str, str | None]:
    """
    Returns (extracted_text, page_count_str).
    page_count_str is None for non-paginated formats.
    """
    ext = Path(filename).suffix.lower()

    if mime_type == "application/pdf" or ext == ".pdf":
        return _extract_pdf(file_bytes)

    if mime_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ) or ext in (".docx", ".doc"):
        return _extract_docx(file_bytes), None

    if mime_type in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ) or ext in (".xlsx", ".xls"):
        return _extract_excel(file_bytes), None

    if mime_type.startswith("text/") or ext in (".txt", ".csv", ".tsv"):
        return file_bytes.decode("utf-8", errors="replace"), None

    # Unsupported format — raise instead of returning empty silently
    raise ValueError(f"Unsupported format for text extraction: {mime_type} ({ext})")


def _extract_pdf(data: bytes) -> tuple[str, str]:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n\n".join(pages), str(len(reader.pages))


def _extract_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_excel(data: bytes) -> str:
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    parts = []
    for sheet in wb.worksheets:
        parts.append(f"[Sheet: {sheet.title}]")
        for row in sheet.iter_rows(values_only=True):
            row_text = "\t".join(str(c) if c is not None else "" for c in row)
            if row_text.strip():
                parts.append(row_text)
    return "\n".join(parts)
