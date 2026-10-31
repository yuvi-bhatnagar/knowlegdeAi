import pytest
from app.ai.factory import AIProviderFactory
from app.core.config import settings
from app.core.exceptions import AIServiceException


def test_factory_invalid_chat_provider_fails():
    with pytest.raises(AIServiceException) as exc_info:
        AIProviderFactory.get_chat_provider(override_provider="nonexistent")
    assert "Unsupported AI chat provider" in str(exc_info.value)
    assert exc_info.value.code == "INVALID_PROVIDER"


def test_factory_invalid_embedding_provider_fails():
    with pytest.raises(AIServiceException) as exc_info:
        AIProviderFactory.get_embedding_provider(override_provider="nonexistent")
    assert "Unsupported AI embedding provider" in str(exc_info.value)
    assert exc_info.value.code == "INVALID_PROVIDER"


def test_factory_openai_missing_key_fails(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    with pytest.raises(AIServiceException) as exc_info:
        AIProviderFactory.get_chat_provider(override_provider="openai")
    assert "OPENAI_API_KEY is not configured" in str(exc_info.value)

    with pytest.raises(AIServiceException) as exc_info:
        AIProviderFactory.get_embedding_provider(override_provider="openai")
    assert "OPENAI_API_KEY is not configured" in str(exc_info.value)


def test_factory_gemini_missing_key_fails(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    with pytest.raises(AIServiceException) as exc_info:
        AIProviderFactory.get_chat_provider(override_provider="gemini")
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)

    with pytest.raises(AIServiceException) as exc_info:
        AIProviderFactory.get_embedding_provider(override_provider="gemini")
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)


def test_factory_ollama_initialization():
    chat_provider = AIProviderFactory.get_chat_provider(override_provider="ollama")
    assert chat_provider.provider_name == "ollama"
    assert chat_provider.model_name == settings.OLLAMA_CHAT_MODEL

    emb_provider = AIProviderFactory.get_embedding_provider(override_provider="ollama")
    assert emb_provider.provider_name == "ollama"
    assert emb_provider.model_name == settings.OLLAMA_EMBEDDING_MODEL

