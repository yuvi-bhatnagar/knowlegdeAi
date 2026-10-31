from app.ai.base import ChatProvider, EmbeddingProvider
from app.ai.providers.openai_provider import OpenAIChatProvider, OpenAIEmbeddingProvider
from app.ai.providers.gemini_provider import GeminiChatProvider, GeminiEmbeddingProvider
from app.ai.providers.ollama_provider import OllamaChatProvider, OllamaEmbeddingProvider
from app.core.config import settings
from app.core.exceptions import AIServiceException
from app.core.logging import logger
from app.core.runtime import RuntimeSettings


class AIProviderFactory:
    """Factory creating decoupled Chat and Embedding providers with strict configuration validation."""

    @classmethod
    def get_chat_provider(cls, override_provider: str | None = None) -> ChatProvider:
        provider_name = (override_provider or RuntimeSettings.get_chat_provider()).lower().strip()

        if provider_name == "openai":
            if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip():
                raise AIServiceException(
                    "OpenAI chat provider selected, but OPENAI_API_KEY is not configured.",
                    status_code=500,
                    code="CONFIG_ERROR",
                )
            return OpenAIChatProvider(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.OPENAI_CHAT_MODEL,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
                max_retries=settings.AI_MAX_RETRIES,
            )

        elif provider_name == "gemini":
            if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
                raise AIServiceException(
                    "Gemini chat provider selected, but GEMINI_API_KEY is not configured.",
                    status_code=500,
                    code="CONFIG_ERROR",
                )
            return GeminiChatProvider(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_CHAT_MODEL,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
                max_retries=settings.AI_MAX_RETRIES,
            )

        elif provider_name == "ollama":
            return OllamaChatProvider(
                base_url=settings.OLLAMA_BASE_URL,
                model_name=settings.OLLAMA_CHAT_MODEL,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
            )

        else:
            raise AIServiceException(
                f"Unsupported AI chat provider '{provider_name}'. Supported providers: 'openai', 'gemini', 'ollama'.",
                status_code=400,
                code="INVALID_PROVIDER",
            )

    @classmethod
    def get_embedding_provider(cls, override_provider: str | None = None) -> EmbeddingProvider:
        provider_name = (override_provider or settings.AI_EMBEDDING_PROVIDER).lower().strip()

        if provider_name == "openai":
            if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip():
                raise AIServiceException(
                    "OpenAI embedding provider selected, but OPENAI_API_KEY is not configured.",
                    status_code=500,
                    code="CONFIG_ERROR",
                )
            return OpenAIEmbeddingProvider(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.OPENAI_EMBEDDING_MODEL,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
                max_retries=settings.AI_MAX_RETRIES,
            )

        elif provider_name == "gemini":
            if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
                raise AIServiceException(
                    "Gemini embedding provider selected, but GEMINI_API_KEY is not configured.",
                    status_code=500,
                    code="CONFIG_ERROR",
                )
            return GeminiEmbeddingProvider(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_EMBEDDING_MODEL,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
                max_retries=settings.AI_MAX_RETRIES,
            )

        elif provider_name == "ollama":
            return OllamaEmbeddingProvider(
                base_url=settings.OLLAMA_BASE_URL,
                model_name=settings.OLLAMA_EMBEDDING_MODEL,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
            )

        else:
            raise AIServiceException(
                f"Unsupported AI embedding provider '{provider_name}'. Supported providers: 'openai', 'gemini', 'ollama'.",
                status_code=400,
                code="INVALID_PROVIDER",
            )

