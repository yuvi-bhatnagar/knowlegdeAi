import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import NormalizedChatMessage
from app.core.exceptions import EntityNotFoundException
from app.core.logging import logger
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.common import PaginatedResponse
from app.schemas.conversation import ConversationResponse, MessageResponse
from app.services.rag_service import RAGService


class ConversationService:
    def __init__(self, session: AsyncSession, rag_service: Optional[RAGService] = None):
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.rag_service = rag_service or RAGService(session)

    async def create_conversation(self, owner_id: uuid.UUID, title: Optional[str] = None) -> ConversationResponse:
        default_title = title.strip() if title and title.strip() else "New Conversation"
        conv = Conversation(
            owner_id=owner_id,
            title=default_title[:255],
        )
        created = await self.conv_repo.create(conv)
        await self.session.commit()
        await self.session.refresh(created)
        return ConversationResponse.model_validate(created)

    async def list_conversations(
        self,
        owner_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[ConversationResponse]:
        items, total = await self.conv_repo.list_by_owner(owner_id, page=page, page_size=page_size)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        return PaginatedResponse(
            items=[ConversationResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_conversation(self, conversation_id: uuid.UUID, owner_id: uuid.UUID) -> ConversationResponse:
        conv = await self.conv_repo.get_by_id_and_owner(conversation_id, owner_id)
        if not conv:
            raise EntityNotFoundException("Conversation", conversation_id)
        return ConversationResponse.model_validate(conv)

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: uuid.UUID,
        title: str,
    ) -> ConversationResponse:
        conv = await self.conv_repo.get_by_id_and_owner(conversation_id, owner_id)
        if not conv:
            raise EntityNotFoundException("Conversation", conversation_id)
        conv.title = title.strip()[:255]
        await self.session.commit()
        await self.session.refresh(conv)
        return ConversationResponse.model_validate(conv)

    async def delete_conversation(self, conversation_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        conv = await self.conv_repo.get_by_id_and_owner(conversation_id, owner_id)
        if not conv:
            raise EntityNotFoundException("Conversation", conversation_id)
        await self.conv_repo.delete(conv)
        await self.session.commit()

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        owner_id: uuid.UUID,
        limit: int = 100,
    ) -> List[MessageResponse]:
        # Validate ownership
        conv = await self.conv_repo.get_by_id_and_owner(conversation_id, owner_id)
        if not conv:
            raise EntityNotFoundException("Conversation", conversation_id)

        messages = await self.conv_repo.get_messages(conversation_id, owner_id, limit=limit)
        return [MessageResponse.model_validate(m) for m in messages]

    async def process_chat(self, request: ChatRequest, owner: User) -> ChatResponse:
        """Processes a chat turn with grounding in uploaded documents and verified citations."""
        conv: Optional[Conversation] = None

        # 1. Resolve or create conversation
        if request.conversation_id:
            conv = await self.conv_repo.get_by_id_and_owner(request.conversation_id, owner.id)
            if not conv:
                raise EntityNotFoundException("Conversation", request.conversation_id)
        else:
            # Auto-create conversation with title based on question
            auto_title = request.question.strip()[:40]
            if len(request.question) > 40:
                auto_title += "..."
            conv = Conversation(owner_id=owner.id, title=auto_title)
            conv = await self.conv_repo.create(conv)
            await self.session.commit()
            await self.session.refresh(conv)

        # 2. Fetch past conversation messages for context budget
        past_messages = await self.conv_repo.get_messages(conv.id, owner.id, limit=10)
        history: List[NormalizedChatMessage] = [
            NormalizedChatMessage(role=m.role, content=m.content)
            for m in past_messages
            if m.role in ["user", "assistant"]
        ]

        # 3. Persist user message in DB
        user_msg = Message(
            conversation_id=conv.id,
            owner_id=owner.id,
            role="user",
            content=request.question,
            sources=[],
        )
        await self.conv_repo.add_message(user_msg)
        await self.session.commit()

        # 4. Execute Grounded RAG with citations
        answer, citations, model_used, insufficient_evidence = await self.rag_service.execute_rag(
            query=request.question,
            owner_id=owner.id,
            document_ids=request.document_ids,
            top_k=request.top_k,
            conversation_history=history,
        )

        # 5. Persist assistant response with verified source citations
        serializable_sources = [c.model_dump(mode="json") for c in citations]
        assistant_msg = Message(
            conversation_id=conv.id,
            owner_id=owner.id,
            role="assistant",
            content=answer,
            sources=serializable_sources,
        )
        saved_assistant = await self.conv_repo.add_message(assistant_msg)
        await self.session.commit()
        await self.session.refresh(saved_assistant)

        return ChatResponse(
            answer=answer,
            conversation_id=conv.id,
            message_id=saved_assistant.id,
            citations=citations,
            model_used=model_used,
            insufficient_evidence=insufficient_evidence,
        )

