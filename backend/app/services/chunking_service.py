from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from app.services.extraction_service import ExtractedPage


@dataclass
class TextChunk:
    chunk_index: int
    page_number: Optional[int]
    content: str
    metadata: Dict[str, Any]


class ChunkingService:
    """Splits extracted document pages into manageable semantic chunks with overlap."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(self, pages: List[ExtractedPage]) -> List[TextChunk]:
        """Split a list of extracted pages into chunks while preserving page numbers."""
        chunks: List[TextChunk] = []
        global_index = 0

        for page in pages:
            raw_text = page.text.strip()
            if not raw_text:
                continue

            # Split text on paragraph or sentence boundaries
            page_chunks = self._split_text(raw_text)
            for text_segment in page_chunks:
                if not text_segment.strip():
                    continue

                chunk = TextChunk(
                    chunk_index=global_index,
                    page_number=page.page_number,
                    content=text_segment.strip(),
                    metadata={
                        "page_number": page.page_number,
                        "chunk_index": global_index,
                        "char_length": len(text_segment.strip()),
                    },
                )
                chunks.append(chunk)
                global_index += 1

        return chunks

    def _split_text(self, text: str) -> List[str]:
        """Recursive chunking splitting on double-newlines, single-newlines, sentence endings, or spaces."""
        if len(text) <= self.chunk_size:
            return [text]

        separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        return self._recursive_split(text, separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        chunks: List[str] = []
        if not separators:
            # Fallback to hard character slicing with overlap
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunks.append(text[start:end])
                if end == len(text):
                    break
                start += self.chunk_size - self.chunk_overlap
            return chunks

        sep = separators[0]
        remaining_seps = separators[1:]

        parts = text.split(sep) if sep else list(text)
        current_chunk = ""

        for part in parts:
            candidate = f"{current_chunk}{sep}{part}" if current_chunk else part
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Carry over overlap
                    overlap_len = min(len(current_chunk), self.chunk_overlap)
                    current_chunk = current_chunk[-overlap_len:] + (sep if sep else "") + part
                    if len(current_chunk) > self.chunk_size:
                        # Part itself exceeds chunk_size, recurse with finer separator
                        sub_chunks = self._recursive_split(part, remaining_seps)
                        chunks.extend(sub_chunks[:-1])
                        current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    sub_chunks = self._recursive_split(part, remaining_seps)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

