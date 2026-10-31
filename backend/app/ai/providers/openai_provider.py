from typing import List, Optional
import httpx
from openai import AsyncOpenAI, APIConnectionError, RateLimitError, AuthenticationError, APIStatusError

from app.ai.base import ChatProvider, EmbeddingProvider, NormalizedChatMessage, NormalizedChatResponse
from app.core.exceptions import AIServiceException
from app.core.logging import logger

# Known default embedding dimensions for OpenAI models
OPENAI_EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


class OpenAIChatProvider(ChatProvider):
    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        if not api_key or not api_key.strip():
            raise AIServiceException("OpenAI API key is missing or empty.")
        self._api_key = api_key
        self._model_name = model_name
        self._client = AsyncOpenAI(
            api_key=api_key,
            timeout=httpx.Timeout(timeout),
            max_retries=max_retries,
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_chat_response(
        self,
        messages: List[NormalizedChatMessage],
        temperature: Optional[float] = 0.2,
        max_tokens: Optional[int] = 2048,
    ) -> NormalizedChatResponse:
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=formatted_messages,
                temperature=temperature if temperature is not None else 0.2,
                max_tokens=max_tokens if max_tokens is not None else 2048,
            )
            choice = response.choices[0]
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            return NormalizedChatResponse(
                content=choice.message.content or "",
                model_name=self._model_name,
                token_usage=usage,
            )
        except AuthenticationError as exc:
            logger.error("OpenAI Authentication error")
            raise AIServiceException("OpenAI authentication failed. Check your API key.", status_code=401)
        except RateLimitError as exc:
            logger.warning(f"OpenAI Rate limit exceeded: {exc}")
            raise AIServiceException("OpenAI rate limit or quota exceeded. Please retry later.", status_code=429)
        except (APIConnectionError, APIStatusError) as exc:
            logger.error(f"OpenAI API error: {exc}")
            raise AIServiceException(f"OpenAI service communication error: {str(exc)}", status_code=502)
        except Exception as exc:
            logger.exception("Unexpected error in OpenAIChatProvider")
            raise AIServiceException(f"Unexpected OpenAI error: {str(exc)}")


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_key: str,
        model_name: str = "text-embedding-3-small",
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        if not api_key or not api_key.strip():
            raise AIServiceException("OpenAI API key is missing or empty.")
        self._api_key = api_key
        self._model_name = model_name
        self._client = AsyncOpenAI(
            api_key=api_key,
            timeout=httpx.Timeout(timeout),
            max_retries=max_retries,
        )
        self._dimension = OPENAI_EMBEDDING_DIMENSIONS.get(model_name, 1536)

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_query(self, text: str) -> List[float]:
        vectors = await self.embed_documents([text])
        return vectors[0]

    async def embed_documents(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        if not texts:
            return []
        try:
            embeddings: List[List[float]] = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response = await self._client.embeddings.create(
                    model=self._model_name,
                    input=batch,
                )
                for item in response.data:
                    embeddings.append(item.embedding)

            # Verify and update dimension if known
            if embeddings and len(embeddings[0]) != self._dimension:
                self._dimension = len(embeddings[0])
            return embeddings
        except AuthenticationError:
            raise AIServiceException("OpenAI authentication failed for embeddings. Verify your OPENAI_API_KEY.", status_code=401)
        except RateLimitError as exc:
            err_msg = str(exc)
            if "quota" in err_msg.lower():
                raise AIServiceException(
                    "OpenAI billing quota exhausted ($0 account balance). Add credits at platform.openai.com/account/billing or switch AI_EMBEDDING_PROVIDER=gemini or ollama in .env.",
                    status_code=429,
                )
            raise AIServiceException(
                f"OpenAI embedding rate limit exceeded (RPM/TPM). Please wait a moment or switch to Gemini/Ollama: {err_msg}",
                status_code=429,
            )
        except Exception as exc:
            raise AIServiceException(f"Failed to generate OpenAI embeddings: {str(exc)}")

