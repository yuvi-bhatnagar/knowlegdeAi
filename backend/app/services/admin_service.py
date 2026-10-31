import uuid
from typing import Any, Dict, List
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import EntityNotFoundException, ValidationException
from app.core.logging import logger
from app.core.runtime import RuntimeSettings
from app.models.chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.models.system_setting import SystemSetting
from app.models.user import User


class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_chat_provider(self) -> str:
        """Retrieves active chat provider from DB settings or falls back to .env default."""
        stmt = select(SystemSetting.value).where(SystemSetting.key == "ai_chat_provider")
        res = await self.session.execute(stmt)
        val = res.scalar_one_or_none()
        provider = val or settings.AI_CHAT_PROVIDER
        RuntimeSettings.set_chat_provider(provider)
        return provider

    async def get_runtime_settings(self) -> Dict[str, Any]:
        """Returns comprehensive runtime settings and provider diagnostic cards."""
        active_chat = await self.get_active_chat_provider()

        providers = [
            {
                "id": "gemini",
                "name": "Google Gemini",
                "model": settings.GEMINI_CHAT_MODEL,
                "is_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip()),
                "is_active": active_chat == "gemini",
                "is_env_default": settings.AI_CHAT_PROVIDER == "gemini",
                "description": "Fast multimodal generation with Google GenAI SDK.",
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "model": settings.OPENAI_CHAT_MODEL,
                "is_configured": bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip()),
                "is_active": active_chat == "openai",
                "is_env_default": settings.AI_CHAT_PROVIDER == "openai",
                "description": "Standard high-performance GPT models from OpenAI.",
            },
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "model": settings.OLLAMA_CHAT_MODEL,
                "is_configured": True,
                "is_active": active_chat == "ollama",
                "is_env_default": settings.AI_CHAT_PROVIDER == "ollama",
                "description": "Self-hosted local models running via Ollama daemon.",
            },
        ]

        return {
            "active_chat_provider": active_chat,
            "env_default_chat_provider": settings.AI_CHAT_PROVIDER,
            "active_embedding_provider": settings.AI_EMBEDDING_PROVIDER,
            "embedding_model": (
                settings.GEMINI_EMBEDDING_MODEL
                if settings.AI_EMBEDDING_PROVIDER == "gemini"
                else settings.OPENAI_EMBEDDING_MODEL
            ),
            "email_provider": settings.EMAIL_PROVIDER,
            "providers": providers,
        }

    async def update_ai_chat_provider(self, new_provider: str) -> Dict[str, Any]:
        """Updates the active AI chat provider dynamically in DB and runtime memory."""
        clean = new_provider.lower().strip()
        if clean not in ("gemini", "openai", "ollama"):
            raise ValidationException(
                f"Unsupported AI chat provider '{new_provider}'. Options: gemini, openai, ollama."
            )

        stmt = select(SystemSetting).where(SystemSetting.key == "ai_chat_provider")
        res = await self.session.execute(stmt)
        setting = res.scalar_one_or_none()

        if setting:
            setting.value = clean
        else:
            setting = SystemSetting(
                key="ai_chat_provider",
                value=clean,
                description="Active AI chat provider selected from admin panel",
            )
            self.session.add(setting)

        await self.session.commit()
        RuntimeSettings.set_chat_provider(clean)

        return await self.get_runtime_settings()

    async def get_system_overview(self) -> Dict[str, Any]:
        """Aggregate platform statistics for the Administrator Dashboard."""
        active_chat = await self.get_active_chat_provider()

        # Users count
        total_users_stmt = select(func.count(User.id))
        total_users = (await self.session.execute(total_users_stmt)).scalar() or 0

        active_users_stmt = select(func.count(User.id)).where(User.is_active == True)
        active_users = (await self.session.execute(active_users_stmt)).scalar() or 0

        # Documents & Chunks count
        total_docs_stmt = select(func.count(Document.id))
        total_docs = (await self.session.execute(total_docs_stmt)).scalar() or 0

        total_chunks_stmt = select(func.count(DocumentChunk.id))
        total_chunks = (await self.session.execute(total_chunks_stmt)).scalar() or 0

        # Conversations & Messages count
        total_convs_stmt = select(func.count(Conversation.id))
        total_convs = (await self.session.execute(total_convs_stmt)).scalar() or 0

        total_msgs_stmt = select(func.count(Message.id))
        total_msgs = (await self.session.execute(total_msgs_stmt)).scalar() or 0

        return {
            "users": {
                "total": total_users,
                "active": active_users,
            },
            "documents": {
                "total": total_docs,
                "chunks": total_chunks,
            },
            "chat": {
                "conversations": total_convs,
                "messages": total_msgs,
                "active_chat_provider": active_chat,
                "env_default_chat_provider": settings.AI_CHAT_PROVIDER,
                "active_embedding_provider": settings.AI_EMBEDDING_PROVIDER,
            },
            "infrastructure": {
                "status": "ready",
                "database": "PostgreSQL",
                "vector_store": "Qdrant",
                "cache_broker": "Redis",
                "email_provider": settings.EMAIL_PROVIDER,
            },
        }

    async def list_users(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Returns paginated users list with their document ingestion counts."""
        offset = (page - 1) * page_size

        total_stmt = select(func.count(User.id))
        total = (await self.session.execute(total_stmt)).scalar() or 0

        users_stmt = (
            select(
                User.id,
                User.email,
                User.is_active,
                User.is_superuser,
                User.role,
                User.created_at,
                func.count(Document.id).label("doc_count"),
            )
            .outerjoin(Document, Document.owner_id == User.id)
            .group_by(User.id)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = (await self.session.execute(users_stmt)).all()

        items = [
            {
                "id": str(r.id),
                "email": r.email,
                "is_active": r.is_active,
                "is_superuser": r.is_superuser,
                "role": r.role,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "document_count": r.doc_count,
            }
            for r in rows
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def toggle_user_status(self, user_id: uuid.UUID, is_active: bool, current_admin_id: uuid.UUID) -> User:
        """Enables or disables a user account. Admins cannot deactivate themselves."""
        if user_id == current_admin_id and not is_active:
            raise ValidationException("Administrators cannot deactivate their own account.")

        stmt = select(User).where(User.id == user_id)
        res = await self.session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise EntityNotFoundException("User", user_id)

        user.is_active = is_active
        await self.session.commit()
        return user

