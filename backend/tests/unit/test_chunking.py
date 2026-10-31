import pytest
from app.services.chunking_service import ChunkingService
from app.services.extraction_service import ExtractedPage, ExtractionService
from app.core.exceptions import DocumentProcessingException
from pathlib import Path
import tempfile


def test_chunking_service_basic():
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    pages = [
        ExtractedPage(page_number=1, text="Hello world! This is a test document to verify chunking."),
        ExtractedPage(page_number=2, text="Second page with more important knowledge for retrieval."),
    ]
    chunks = service.chunk_pages(pages)
    assert len(chunks) >= 2
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
    assert "Hello world!" in chunks[0].content


def test_chunking_service_overlap_and_bounds():
    service = ChunkingService(chunk_size=50, chunk_overlap=10)
    long_text = "Word " * 50  # 250 characters
    pages = [ExtractedPage(page_number=1, text=long_text)]
    chunks = service.chunk_pages(pages)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.content) <= 60  # close to chunk_size bound


def test_chunking_invalid_overlap_raises():
    with pytest.raises(ValueError):
        ChunkingService(chunk_size=100, chunk_overlap=100)


def test_extraction_service_txt_file():
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Line 1\nLine 2\nLine 3")
        temp_path = Path(f.name)

    try:
        pages = ExtractionService.extract_text(temp_path, "text/plain", "sample.txt")
        assert len(pages) == 1
        assert pages[0].page_number == 1
        assert "Line 1" in pages[0].text
    finally:
        temp_path.unlink()


def test_extraction_service_empty_txt_raises():
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("   \n\t  ")
        temp_path = Path(f.name)

    try:
        with pytest.raises(DocumentProcessingException):
            ExtractionService.extract_text(temp_path, "text/plain", "empty.txt")
    finally:
        temp_path.unlink()

