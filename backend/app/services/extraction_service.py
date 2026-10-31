from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import pymupdf  # Official PyMuPDF import

from app.core.exceptions import DocumentProcessingException
from app.core.logging import logger


@dataclass
class ExtractedPage:
    page_number: Optional[int]
    text: str


class ExtractionService:
    """Extracts text content and page metadata from PDF, TXT, and Markdown documents."""

    SUPPORTED_MIME_TYPES = {
        "application/pdf": "pdf",
        "text/plain": "txt",
        "text/markdown": "md",
        "application/octet-stream": "binary",
    }

    @classmethod
    def extract_text(cls, file_path: Path, mime_type: str, original_filename: str) -> List[ExtractedPage]:
        """Extract pages/sections from a file. Returns list of ExtractedPage objects."""
        if not file_path.exists():
            raise DocumentProcessingException(f"Document file not found at {file_path}")

        ext = file_path.suffix.lower().lstrip(".")
        if ext == "pdf" or mime_type == "application/pdf":
            return cls._extract_pdf(file_path)
        elif ext in ["txt", "md", "markdown"] or mime_type in ["text/plain", "text/markdown"]:
            return cls._extract_text_file(file_path)
        else:
            raise DocumentProcessingException(
                f"Unsupported file format '{ext}' (MIME: {mime_type}). Only PDF, TXT, and Markdown files are supported."
            )

    @classmethod
    def _extract_pdf(cls, file_path: Path) -> List[ExtractedPage]:
        pages: List[ExtractedPage] = []
        try:
            doc = pymupdf.open(file_path)
        except Exception as exc:
            logger.warning(f"Failed to open PDF file: {exc}")
            raise DocumentProcessingException(f"Invalid or corrupted PDF file: {str(exc)}")

        if doc.is_encrypted:
            try:
                # Attempt empty password decrypt
                if not doc.authenticate(""):
                    raise DocumentProcessingException("Password-protected or encrypted PDFs are not supported.")
            except Exception:
                raise DocumentProcessingException("Password-protected or encrypted PDFs are not supported.")

        total_extracted_chars = 0
        for page_idx in range(len(doc)):
            page = doc.load_page(page_idx)
            text = page.get_text("text").strip()
            total_extracted_chars += len(text)
            if text:
                pages.append(ExtractedPage(page_number=page_idx + 1, text=text))

        doc.close()

        if total_extracted_chars == 0:
            raise DocumentProcessingException(
                "No readable text found in PDF. Scanned documents or image-only PDFs without an OCR text layer are not supported."
            )

        return pages

    @classmethod
    def _extract_text_file(cls, file_path: Path) -> List[ExtractedPage]:
        # Try UTF-8 with fallback to latin-1
        content = ""
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding="latin-1")
            except Exception as exc:
                raise DocumentProcessingException(f"Could not decode text file: {str(exc)}")

        cleaned = content.strip()
        if not cleaned:
            raise DocumentProcessingException("Uploaded document contains no text content.")

        # Text files do not have physical page numbers; represent as page 1
        return [ExtractedPage(page_number=1, text=cleaned)]

