import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    ConversationUpdateRequest,
    MessageResponse,
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ConversationResponse:
    """Create a new chat conversation thread."""
    service = ConversationService(session)
    return await service.create_conversation(owner_id=current_user.id, title=data.title)


@router.get("", response_model=PaginatedResponse[ConversationResponse])
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[ConversationResponse]:
    """List conversations owned by authenticated user."""
    service = ConversationService(session)
    return await service.list_conversations(owner_id=current_user.id, page=page, page_size=page_size)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ConversationResponse:
    """Retrieve details for a single conversation."""
    service = ConversationService(session)
    return await service.get_conversation(conversation_id=conversation_id, owner_id=current_user.id)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: uuid.UUID,
    data: ConversationUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ConversationResponse:
    """Rename conversation title."""
    service = ConversationService(session)
    return await service.update_conversation(
        conversation_id=conversation_id, owner_id=current_user.id, title=data.title
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a conversation and all its messages."""
    service = ConversationService(session)
    await service.delete_conversation(conversation_id=conversation_id, owner_id=current_user.id)


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=200, description="Max messages to retrieve"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> List[MessageResponse]:
    """Retrieve message history for a conversation."""
    service = ConversationService(session)
    return await service.get_messages(
        conversation_id=conversation_id, owner_id=current_user.id, limit=limit
    )

