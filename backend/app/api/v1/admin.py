import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin Management"])


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency verifying that the user has administrator privileges."""
    if not (current_user.is_superuser or current_user.role == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: administrator privileges required.",
        )
    return current_user


class UpdateChatProviderRequest(BaseModel):
    provider: str = Field(..., description="Target AI Chat Provider (gemini, openai, ollama)")


class ToggleUserStatusRequest(BaseModel):
    is_active: bool = Field(..., description="Activate or deactivate user account")


@router.get("/overview")
async def get_admin_overview(
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Retrieve system status, infrastructure readiness, and platform-wide metrics."""
    service = AdminService(session)
    return await service.get_system_overview()


@router.get("/settings")
async def get_admin_settings(
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Retrieve dynamic runtime configuration and provider options."""
    service = AdminService(session)
    return await service.get_runtime_settings()


@router.patch("/settings/ai-chat-provider")
async def update_ai_chat_provider(
    data: UpdateChatProviderRequest,
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Update active AI chat provider dynamically without restart."""
    service = AdminService(session)
    return await service.update_ai_chat_provider(data.provider)


@router.get("/users")
async def list_admin_users(
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """List registered users with status and document counts."""
    service = AdminService(session)
    return await service.list_users(page=page, page_size=page_size)


@router.patch("/users/{user_id}/status")
async def toggle_user_status(
    user_id: uuid.UUID,
    data: ToggleUserStatusRequest,
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Enable or disable a user account."""
    service = AdminService(session)
    user = await service.toggle_user_status(user_id, data.is_active, admin.id)
    return {
        "id": str(user.id),
        "email": user.email,
        "is_active": user.is_active,
        "message": f"User status successfully updated to {'active' if user.is_active else 'inactive'}.",
    }

