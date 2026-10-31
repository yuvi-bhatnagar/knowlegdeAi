from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedChatMessage:
    role: str  # 'system', 'user', 'assistant'
    content: str


@dataclass
class NormalizedChatResponse:
    content: str
    model_name: str
    token_usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Optional[Dict[str, Any]] = None


class ChatProvider(ABC):
    """Abstract interface for AI chat generation providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider, e.g. 'openai', 'gemini', 'ollama'."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier, e.g. 'gpt-4o-mini', 'gemini-1.5-flash'."""
        pass

    @abstractmethod
    async def generate_chat_response(
        self,
        messages: List[NormalizedChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> NormalizedChatResponse:
        """Generate response given conversation history and context."""
        pass


class EmbeddingProvider(ABC):
    """Abstract interface for text embedding generation providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider, e.g. 'openai', 'gemini', 'ollama'."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Embedding model identifier."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector embedding output dimensions."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for a single search query."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of document chunks."""
        pass

