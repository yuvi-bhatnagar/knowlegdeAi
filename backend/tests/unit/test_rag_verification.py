import uuid
import pytest
from app.schemas.chat import Citation
from app.services.rag_service import RAGService, INSUFFICIENT_EVIDENCE_PHRASE
from unittest.mock import MagicMock


def test_verify_citations_valid_reference():
    service = RAGService(session=MagicMock(), vector_service=MagicMock())
    doc_id = str(uuid.uuid4())

    retrieved_chunks = [
        {
            "document_id": doc_id,
            "chunk_index": 0,
            "page_number": 3,
            "filename": "python_guide.pdf",
            "content": "Python 3.12 introduces improved error messages.",
            "score": 0.88,
        },
        {
            "document_id": doc_id,
            "chunk_index": 1,
            "page_number": 4,
            "filename": "python_guide.pdf",
            "content": "Asyncio provides event loops and task management.",
            "score": 0.82,
        },
    ]

    answer = "Python 3.12 has better errors [Chunk 0], and asyncio handles tasks [Chunk 1]."
    citations = service._verify_citations(answer, retrieved_chunks)

    assert len(citations) == 2
    assert citations[0].chunk_index == 0
    assert citations[0].page_number == 3
    assert citations[0].filename == "python_guide.pdf"
    assert "Python 3.12" in citations[0].excerpt

    assert citations[1].chunk_index == 1
    assert citations[1].page_number == 4


def test_verify_citations_rejects_hallucinated_ids():
    service = RAGService(session=MagicMock(), vector_service=MagicMock())
    doc_id = str(uuid.uuid4())

    retrieved_chunks = [
        {
            "document_id": doc_id,
            "chunk_index": 0,
            "page_number": 1,
            "filename": "doc.txt",
            "content": "Only chunk available in retrieved set.",
            "score": 0.9,
        }
    ]

    # Model hallucinates chunk 5 and chunk 99
    answer = "Here is some made-up claim [Chunk 5] and [Chunk 99]."
    citations = service._verify_citations(answer, retrieved_chunks)

    # Hallucinated indices 5 and 99 do not exist; fallback provides available real chunk 0
    for citation in citations:
        assert citation.chunk_index == 0


def test_insufficient_evidence_phrase_constant():
    assert "sufficient evidence" in INSUFFICIENT_EVIDENCE_PHRASE.lower()
    assert "cannot find" in INSUFFICIENT_EVIDENCE_PHRASE.lower()


def test_conversational_and_meta_query_detection():
    from app.services.rag_service import is_conversational_or_meta_query
    # Greetings & meta queries should return True
    assert is_conversational_or_meta_query("Hi") is True
    assert is_conversational_or_meta_query("Hello there!") is True
    assert is_conversational_or_meta_query("Who are you?") is True
    assert is_conversational_or_meta_query("Can you only chat based on the document only?") is True
    assert is_conversational_or_meta_query("How does this work?") is True

    # Factual document queries should return False
    assert is_conversational_or_meta_query("What was the net revenue in Q3 2023?") is False
    assert is_conversational_or_meta_query("Explain clause 4 of the employment agreement.") is False
