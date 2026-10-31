import hashlib
import re
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import AIProviderFactory
from app.core.config import settings
from app.core.exceptions import (
    DocumentProcessingException,
    EntityAlreadyExistsException,
    EntityNotFoundException,
    ValidationException,
)
from app.core.logging import logger
from app.models.document import Document
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.schemas.common import PaginatedResponse
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.vector_service import VectorService
from app.workers.document_tasks import process_document_task


class DocumentService:
    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/octet-stream",
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)

    async def upload_document(self, file: UploadFile, owner: User) -> DocumentUploadResponse:
        """Validate, store, register, and queue a document for ingestion."""
        # 1. Filename & extension validation
        original_filename = file.filename or "uploaded_file"
        # Sanitize filename
        clean_filename = re.sub(r"[^\w\.\-]", "_", Path(original_filename).name)
        ext = Path(clean_filename).suffix.lower()

        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationException(
                f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # 2. Read content & validate file size
        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise ValidationException("Uploaded file is empty.")

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise ValidationException(f"File size exceeds maximum allowed limit of {max_mb} MB.")

        # 3. Compute SHA256 checksum and check duplicates
        checksum = hashlib.sha256(content).hexdigest()
        existing = await self.doc_repo.get_by_checksum_and_owner(checksum, owner.id)
        if existing and existing.status in ["uploaded", "processing", "completed"]:
            raise EntityAlreadyExistsException(
                f"You have already uploaded an identical document: '{existing.original_filename}'."
            )

        # 4. Save file to disk with server-generated key
        user_storage_dir = settings.storage_path / str(owner.id)
        user_storage_dir.mkdir(parents=True, exist_ok=True)

        storage_filename = f"{uuid.uuid4()}_{clean_filename}"
        storage_path = user_storage_dir / storage_filename
        storage_path.write_bytes(content)

        # 5. Determine MIME type
        mime_type = file.content_type or "application/octet-stream"

        # 6. Create database record
        doc = Document(
            owner_id=owner.id,
            original_filename=clean_filename,
            storage_key=str(storage_path.resolve()),
            mime_type=mime_type,
            file_size=file_size,
            checksum=checksum,
            status="uploaded",
        )
        created_doc = await self.doc_repo.create(doc)
        await self.session.commit()
        await self.session.refresh(created_doc)

        # 7. Enqueue background ingestion
        try:
            process_document_task.delay(str(created_doc.id))
            logger.info(f"Queued Celery processing task for document {created_doc.id}")
        except Exception as exc:
            logger.warning(
                f"Could not reach Celery broker ({exc}). The task will remain in 'uploaded' state until picked up or processed."
            )

        return DocumentUploadResponse(
            id=created_doc.id,
            original_filename=created_doc.original_filename,
            status=created_doc.status,
            message="Document uploaded successfully and queued for indexing.",
        )

    async def get_document(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> DocumentResponse:
        doc = await self.doc_repo.get_by_id_and_owner(document_id, owner_id)
        if not doc:
            raise EntityNotFoundException("Document", document_id)
        return DocumentResponse.model_validate(doc)

    async def list_documents(
        self,
        owner_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[DocumentResponse]:
        items, total = await self.doc_repo.list_by_owner(owner_id, page=page, page_size=page_size)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        return PaginatedResponse(
            items=[DocumentResponse.model_validate(d) for d in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def delete_document(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        doc = await self.doc_repo.get_by_id_and_owner(document_id, owner_id)
        if not doc:
            raise EntityNotFoundException("Document", document_id)

        # 1. Clean up vector embeddings in Qdrant
        try:
            embedding_provider = AIProviderFactory.get_embedding_provider()
            collection_name = VectorService.get_collection_name(
                model_name=embedding_provider.model_name,
                dimension=embedding_provider.dimension,
            )
            vector_service = VectorService()
            await vector_service.delete_by_document(collection_name, doc.id, owner_id)
        except Exception as exc:
            logger.warning(f"Could not clean up vectors for document {document_id}: {exc}")

        # 2. Remove physical file
        try:
            p = Path(doc.storage_key)
            if p.exists():
                p.unlink()
        except Exception as exc:
            logger.warning(f"Failed to delete document file {doc.storage_key}: {exc}")

        # 3. Delete database record (cascades to chunks)
        await self.doc_repo.delete(doc)
        await self.session.commit()
        logger.info(f"Deleted document {document_id} and associated chunks/vectors.")

    async def retry_document(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> DocumentResponse:
        doc = await self.doc_repo.get_by_id_and_owner(document_id, owner_id)
        if not doc:
            raise EntityNotFoundException("Document", document_id)

        doc.status = "uploaded"
        doc.error_summary = None
        await self.session.commit()
        await self.session.refresh(doc)

        try:
            process_document_task.delay(str(doc.id))
        except Exception as exc:
            logger.warning(f"Could not reach Celery broker for retry: {exc}")

        return DocumentResponse.model_validate(doc)

