import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)

    async def get_by_id_and_owner(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> Optional[Document]:
        stmt = select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_checksum_and_owner(self, checksum: str, owner_id: uuid.UUID) -> Optional[Document]:
        stmt = select(Document).where(Document.checksum == checksum, Document.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        owner_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Document], int]:
        count_stmt = select(func.count(Document.id)).where(Document.owner_id == owner_id)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            select(Document)
            .where(Document.owner_id == owner_id)
            .order_by(desc(Document.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def count_by_owner(self, owner_id: uuid.UUID) -> int:
        stmt = select(func.count(Document.id)).where(Document.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        self.session.add_all(chunks)
        await self.session.flush()

    async def get_chunks_for_document(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> List[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id, DocumentChunk.owner_id == owner_id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_chunks_by_vector_ids(self, vector_ids: List[str], owner_id: uuid.UUID) -> List[DocumentChunk]:
        if not vector_ids:
            return []
        stmt = select(DocumentChunk).where(
            DocumentChunk.vector_id.in_(vector_ids),
            DocumentChunk.owner_id == owner_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
