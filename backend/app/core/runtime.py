from app.core.config import settings
from app.core.logging import logger


class RuntimeSettings:
    """Thread-safe in-memory cache for dynamic runtime settings backed by database and .env defaults."""

    _active_chat_provider: str | None = None

    @classmethod
    def get_chat_provider(cls) -> str:
        """Returns the currently active AI chat provider (runtime selection or .env default)."""
        return cls._active_chat_provider or settings.AI_CHAT_PROVIDER

    @classmethod
    def set_chat_provider(cls, provider: str) -> None:
        """Dynamically switches the active AI chat provider at runtime."""
        clean_provider = provider.lower().strip()
        logger.info(
            f"🔄 [Runtime Settings] AI Chat Provider switched: "
            f"'{cls._active_chat_provider or settings.AI_CHAT_PROVIDER}' -> '{clean_provider}'"
        )
        cls._active_chat_provider = clean_provider

