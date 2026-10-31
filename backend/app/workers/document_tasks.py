import asyncio
import uuid
from pathlib import Path
from typing import List
from qdrant_client.http import models as qmodels
from sqlalchemy import select

from app.ai.factory import AIProviderFactory
from app.core.exceptions import DocumentProcessingException
from app.core.logging import logger
from app.db.session import async_session_factory
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.services.chunking_service import ChunkingService
from app.services.extraction_service import ExtractionService
from app.services.vector_service import VectorService
from app.workers.celery_app import celery_app


def format_safe_error_summary(exc: Exception) -> str:
    """Sanitizes exceptions into clean, human-readable user messages without raw JSON or tracebacks."""
    err_str = str(exc)
    err_lower = err_str.lower()

    if "429" in err_str or "resource_exhausted" in err_lower or "quota" in err_lower or "rate limit" in err_lower:
        return (
            "Provider embedding quota temporarily reached on Free Tier. "
            "Please click 'Retry Ingestion' in 1 minute, or switch AI providers in the Admin Console."
        )

    if "not found" in err_lower or "404" in err_str:
        return (
            "The configured AI embedding model is unavailable with your provider. "
            "Please check model settings in the Admin Console."
        )

    if "401" in err_str or "403" in err_str or "api key" in err_lower or "unauthorized" in err_lower:
        return "AI Provider authentication failed. Please verify your API key in configuration."

    if "no text chunks" in err_lower or "empty" in err_lower:
        return "No readable text could be extracted. If this is a scanned/image PDF, optical character recognition (OCR) is required."

    if isinstance(exc, DocumentProcessingException):
        return exc.message

    return "Document processing encountered an error during ingestion. Please retry or verify the file format."


async def process_document_pipeline(document_id_str: str) -> bool:
    """Async business logic that executes the complete document ingestion pipeline."""
    doc_id = uuid.UUID(document_id_str)

    async with async_session_factory() as session:
        # 1. Fetch document record
        result = await session.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            logger.error(f"Document {doc_id} not found in database for ingestion task.")
            return False

        # Idempotency check: if already completed, exit safely
        if doc.status == "completed":
            logger.info(f"Document {doc_id} already marked completed. Skipping.")
            return True

        # 2. Update status to processing
        doc.status = "processing"
        doc.error_summary = None
        await session.commit()

        file_path = Path(doc.storage_key)
        vector_service = VectorService()
        collection_name = None

        try:
            # 3. Text Extraction
            pages = ExtractionService.extract_text(
                file_path=file_path,
                mime_type=doc.mime_type,
                original_filename=doc.original_filename,
            )

            # 4. Semantic Chunking
            from app.core.config import settings

            chunker = ChunkingService(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            text_chunks = chunker.chunk_pages(pages)

            if not text_chunks:
                raise DocumentProcessingException("No text chunks generated from document.")

            # 5. Embedding Generation
            embedding_provider = AIProviderFactory.get_embedding_provider()
            collection_name = VectorService.get_collection_name(
                model_name=embedding_provider.model_name,
                dimension=embedding_provider.dimension,
            )

            # Ensure Qdrant collection is ready
            await vector_service.ensure_collection(
                collection_name=collection_name,
                vector_size=embedding_provider.dimension,
            )

            chunk_texts = [c.content for c in text_chunks]
            embeddings = await embedding_provider.embed_documents(chunk_texts)

            if len(embeddings) != len(text_chunks):
                raise DocumentProcessingException(
                    f"Mismatch between chunks ({len(text_chunks)}) and embeddings ({len(embeddings)})"
                )

            # 6. Prepare Qdrant Points and DB Chunks
            points: List[qmodels.PointStruct] = []
            db_chunks: List[DocumentChunk] = []

            for idx, (chunk, vector) in enumerate(zip(text_chunks, embeddings)):
                vector_uuid = str(uuid.uuid4())
                point = qmodels.PointStruct(
                    id=vector_uuid,
                    vector=vector,
                    payload={
                        "owner_id": str(doc.owner_id),
                        "document_id": str(doc.id),
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number,
                        "filename": doc.original_filename,
                        "content": chunk.content,
                    },
                )
                points.append(point)

                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    owner_id=doc.owner_id,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    content=chunk.content,
                    vector_id=vector_uuid,
                    chunk_metadata=chunk.metadata,
                )
                db_chunks.append(db_chunk)

            # 7. Upsert to Vector Store
            await vector_service.upsert_chunks(collection_name, points)

            # 8. Save chunks in Database and mark completed
            session.add_all(db_chunks)
            doc.chunk_count = len(db_chunks)
            doc.status = "completed"
            await session.commit()
            logger.info(f"Document {doc.id} ('{doc.original_filename}') successfully processed with {len(db_chunks)} chunks.")
            return True

        except Exception as exc:
            logger.exception(f"Document processing failed for {doc_id}: {exc}")
            await session.rollback()

            # Mark document as failed with clean, safe error summary
            safe_error_summary = format_safe_error_summary(exc)
            async with async_session_factory() as error_session:
                res = await error_session.execute(select(Document).where(Document.id == doc_id))
                failed_doc = res.scalar_one_or_none()
                if failed_doc:
                    failed_doc.status = "failed"
                    failed_doc.error_summary = safe_error_summary
                    await error_session.commit()

            # Clean up any partial vectors
            if collection_name:
                try:
                    await vector_service.delete_by_document(collection_name, doc.id, doc.owner_id)
                except Exception:
                    pass

            return False


@celery_app.task(
    bind=True,
    name="app.workers.document_tasks.process_document_task",
    max_retries=2,
    default_retry_delay=10,
)
def process_document_task(self, document_id_str: str):
    """Celery worker task wrapping the async document ingestion pipeline."""
    logger.info(f"Celery task started for document: {document_id_str}")
    try:
        success = asyncio.run(process_document_pipeline(document_id_str))
        if not success:
            logger.warning(f"Pipeline returned failure for {document_id_str}")
    except Exception as exc:
        logger.error(f"Celery task encountered unhandled exception: {exc}")
        raise self.retry(exc=exc)

