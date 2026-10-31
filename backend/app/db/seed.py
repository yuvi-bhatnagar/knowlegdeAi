import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.security import get_password_hash
from app.db.session import async_session_factory
from app.models.system_setting import SystemSetting
from app.models.user import User

ADMIN_EMAIL = "admin_knowledge_36@knowledge.ai"
ADMIN_PASSWORD = "Test!234"


async def seed_admin_and_settings(session: AsyncSession) -> None:
    """Seed the administrator user and initial system settings if not already present."""
    # 1. Seed or update the administrator account
    stmt = select(User).where(User.email == ADMIN_EMAIL)
    res = await session.execute(stmt)
    admin_user = res.scalar_one_or_none()

    if not admin_user:
        logger.info(f"Seeding default admin user: {ADMIN_EMAIL}")
        admin_user = User(
            id=uuid.uuid4(),
            email=ADMIN_EMAIL,
            password_hash=get_password_hash(ADMIN_PASSWORD),
            is_active=True,
            is_superuser=True,
            role="admin",
        )
        session.add(admin_user)
    else:
        # Ensure administrator rights are up to date
        admin_user.is_superuser = True
        admin_user.role = "admin"
        admin_user.is_active = True

    # 2. Seed initial runtime system settings
    # Active AI Chat Provider: defaults to .env setting (e.g. gemini)
    chat_prov_stmt = select(SystemSetting).where(SystemSetting.key == "ai_chat_provider")
    res_chat = await session.execute(chat_prov_stmt)
    chat_setting = res_chat.scalar_one_or_none()

    if not chat_setting:
        logger.info(f"Seeding default system setting: ai_chat_provider = {settings.AI_CHAT_PROVIDER}")
        chat_setting = SystemSetting(
            key="ai_chat_provider",
            value=settings.AI_CHAT_PROVIDER,
            description="Active AI Chat Provider selectable at runtime (gemini, openai, ollama)",
        )
        session.add(chat_setting)

    # Active AI Embedding Provider
    embed_prov_stmt = select(SystemSetting).where(SystemSetting.key == "ai_embedding_provider")
    res_embed = await session.execute(embed_prov_stmt)
    embed_setting = res_embed.scalar_one_or_none()

    if not embed_setting:
        embed_setting = SystemSetting(
            key="ai_embedding_provider",
            value=settings.AI_EMBEDDING_PROVIDER,
            description="Active AI Embedding Provider",
        )
        session.add(embed_setting)

    await session.commit()
    logger.info("Admin user and system settings verified successfully.")


async def run_seed() -> None:
    async with async_session_factory() as session:
        await seed_admin_and_settings(session)


if __name__ == "__main__":
    asyncio.run(run_seed())

