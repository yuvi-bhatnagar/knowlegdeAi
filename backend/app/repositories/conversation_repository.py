import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)

    async def get_by_id_and_owner(self, conversation_id: uuid.UUID, owner_id: uuid.UUID) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conversation_id, Conversation.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        owner_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Conversation], int]:
        count_stmt = select(func.count(Conversation.id)).where(Conversation.owner_id == owner_id)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            select(Conversation)
            .where(Conversation.owner_id == owner_id)
            .order_by(desc(Conversation.updated_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def count_by_owner(self, owner_id: uuid.UUID) -> int:
        stmt = select(func.count(Conversation.id)).where(Conversation.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add_message(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        owner_id: uuid.UUID,
        limit: int = 100,
    ) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.owner_id == owner_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
