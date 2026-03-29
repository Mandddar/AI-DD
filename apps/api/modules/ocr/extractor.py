"""
Text extraction from uploaded documents.
Supports: PDF, Word (.docx), Excel (.xlsx/.xls), CSV, TSV, plain text, Images.

Libraries:
  - pymupdf (fitz) — PDF parsing + PDF-to-image for OCR fallback
  - python-docx — Word .docx parsing
  - openpyxl — Excel .xlsx parsing
  - pandas — CSV / TSV parsing
  - pytesseract + Pillow — OCR for scanned/image documents
"""
import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


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

    if ext in (".csv", ".tsv") or mime_type in ("text/csv", "text/tab-separated-values"):
        return _extract_csv_tsv(file_bytes, ext), None

    if mime_type.startswith("text/") or ext == ".txt":
        return file_bytes.decode("utf-8", errors="replace"), None

    if mime_type.startswith("image/") or ext in (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"):
        return _extract_image_ocr(file_bytes), None

    return "", None


def _extract_pdf(data: bytes) -> tuple[str, str]:
    """Extract text from PDF using pymupdf. Falls back to OCR for scanned pages."""
    import fitz  # pymupdf

    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            pages.append(text)
        else:
            # Scanned page — OCR fallback via pytesseract
            try:
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                ocr_text = _ocr_image_bytes(img_bytes)
                if ocr_text.strip():
                    pages.append(ocr_text)
            except Exception as e:
                logger.warning("OCR fallback failed for page %d: %s", page.number, e)
    doc.close()
    return "\n\n".join(pages), str(doc.page_count)


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


def _extract_csv_tsv(data: bytes, ext: str) -> str:
    """Parse CSV/TSV files using pandas."""
    import pandas as pd
    sep = "\t" if ext == ".tsv" else ","
    try:
        df = pd.read_csv(io.BytesIO(data), sep=sep)
        return df.to_string(index=False)
    except Exception as e:
        logger.warning("pandas CSV/TSV parse failed: %s, falling back to raw text", e)
        return data.decode("utf-8", errors="replace")


def _extract_image_ocr(data: bytes) -> str:
    """OCR an image file using pytesseract + Pillow."""
    return _ocr_image_bytes(data)


def _ocr_image_bytes(img_bytes: bytes) -> str:
    """Run pytesseract OCR on raw image bytes."""
    try:
        from PIL import Image
        import pytesseract
        image = Image.open(io.BytesIO(img_bytes))
        return pytesseract.image_to_string(image, lang="eng")
    except Exception as e:
        logger.error("pytesseract OCR failed: %s", e)
        return ""
