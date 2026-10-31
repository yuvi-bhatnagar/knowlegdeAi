from typing import List, Optional
import httpx

from app.ai.base import ChatProvider, EmbeddingProvider, NormalizedChatMessage, NormalizedChatResponse
from app.core.exceptions import AIServiceException
from app.core.logging import logger

OLLAMA_DEFAULT_EMBEDDING_DIMENSIONS = {
    "nomic-embed-text": 768,
    "all-minilm": 384,
    "mxbai-embed-large": 1024,
    "bge-m3": 1024,
}


class OllamaChatProvider(ChatProvider):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3.2",
        timeout: float = 60.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_chat_response(
        self,
        messages: List[NormalizedChatMessage],
        temperature: Optional[float] = 0.2,
        max_tokens: Optional[int] = 2048,
    ) -> NormalizedChatResponse:
        payload = {
            "model": self._model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else 0.2,
                "num_predict": max_tokens if max_tokens is not None else 2048,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                res = await client.post(f"{self._base_url}/api/chat", json=payload)
                if res.status_code != 200:
                    raise AIServiceException(f"Ollama returned error status {res.status_code}: {res.text}")
                data = res.json()
                content = data.get("message", {}).get("content", "")
                usage = {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                }
                return NormalizedChatResponse(
                    content=content,
                    model_name=self._model_name,
                    token_usage=usage,
                )
        except httpx.ConnectError:
            raise AIServiceException(
                f"Could not connect to Ollama at {self._base_url}. Ensure Ollama is running.",
                status_code=503,
            )
        except Exception as exc:
            raise AIServiceException(f"Ollama chat error: {str(exc)}")


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "nomic-embed-text",
        timeout: float = 60.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout = timeout
        self._dimension = OLLAMA_DEFAULT_EMBEDDING_DIMENSIONS.get(model_name, 768)

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_query(self, text: str) -> List[float]:
        vectors = await self.embed_documents([text])
        return vectors[0]

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            embeddings: List[List[float]] = []
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                for text in texts:
                    res = await client.post(
                        f"{self._base_url}/api/embeddings",
                        json={"model": self._model_name, "prompt": text},
                    )
                    if res.status_code != 200:
                        raise AIServiceException(f"Ollama embeddings error: {res.text}")
                    emb = res.json().get("embedding", [])
                    embeddings.append(emb)
                    if emb:
                        self._dimension = len(emb)
            return embeddings
        except httpx.ConnectError:
            raise AIServiceException(
                f"Could not connect to Ollama at {self._base_url} for embeddings.",
                status_code=503,
            )
        except Exception as exc:
            raise AIServiceException(f"Ollama embedding error: {str(exc)}")

