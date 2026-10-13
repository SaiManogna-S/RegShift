"""
Text extraction service for PDF and TXT files.
"""
import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text(file_path: str, file_type: str) -> tuple[str, str | None]:
    """
    Extract text from a document file.
    Returns (extracted_text, error_message).
    error_message is None on success.
    """
    path = Path(file_path)
    if not path.exists():
        return "", f"File not found: {file_path}"

    if file_type == "text/plain" or path.suffix.lower() == ".txt":
        return _extract_txt(path)
    elif file_type == "application/pdf" or path.suffix.lower() == ".pdf":
        return _extract_pdf(path)
    else:
        return "", f"Unsupported file type: {file_type}"


def _extract_txt(path: Path) -> tuple[str, str | None]:
    try:
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                text = path.read_text(encoding=encoding)
                if text.strip():
                    return text, None
            except UnicodeDecodeError:
                continue
        return "", "Could not decode text file with any supported encoding."
    except Exception as e:
        logger.exception("TXT extraction failed")
        return "", f"Text extraction error: {str(e)}"


def _extract_pdf(path: Path) -> tuple[str, str | None]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            return "", "PDF is encrypted and cannot be read without a password."

        pages_text = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(f"[Page {i + 1}]\n{text.strip()}")
            except Exception as page_err:
                logger.warning(f"Failed to extract page {i+1}: {page_err}")
                pages_text.append(f"[Page {i + 1}]\n[Could not extract text from this page]")

        if not pages_text:
            return "", (
                "No text could be extracted from this PDF. "
                "It may be a scanned image-based PDF. "
                "OCR is not available in this version — please provide a text-based PDF or a TXT file."
            )

        full_text = "\n\n".join(pages_text)
        return full_text, None

    except ImportError:
        return "", "pypdf library is not installed. Cannot extract PDF text."
    except Exception as e:
        logger.exception("PDF extraction failed")
        return "", f"PDF extraction error: {str(e)}"
