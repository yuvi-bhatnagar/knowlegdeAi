import asyncio
import re
from typing import List, Optional
from google import genai
from google.genai import types

from app.ai.base import ChatProvider, EmbeddingProvider, NormalizedChatMessage, NormalizedChatResponse
from app.core.exceptions import AIServiceException
from app.core.logging import logger

GEMINI_EMBEDDING_DIMENSIONS = {
    "gemini-embedding-001": 3072,
    "models/gemini-embedding-001": 3072,
    "gemini-embedding-2-preview": 3072,
    "gemini-embedding-2": 3072,
    "text-embedding-004": 768,
    "embedding-001": 768,
}


class GeminiChatProvider(ChatProvider):
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        if not api_key or not api_key.strip():
            raise AIServiceException("Gemini API key is missing or empty.")
        self._api_key = api_key
        # Automatically upgrade legacy 1.5 model name to 2.5 flash supported in API
        if model_name in ["gemini-1.5-flash", "gemini-1.5-pro"]:
            self._model_name = "gemini-2.5-flash"
        else:
            self._model_name = model_name
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = genai.Client(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_chat_response(
        self,
        messages: List[NormalizedChatMessage],
        temperature: Optional[float] = 0.2,
        max_tokens: Optional[int] = 2048,
    ) -> NormalizedChatResponse:
        system_instruction = ""
        contents = []

        for msg in messages:
            if msg.role == "system":
                system_instruction += msg.content + "\n"
            elif msg.role in ["user", "assistant"]:
                role = "user" if msg.role == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))

        # If only system messages were passed or no contents, create a placeholder user turn
        if not contents:
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text="Hello")]))

        config = types.GenerateContentConfig(
            temperature=temperature if temperature is not None else 0.2,
            max_output_tokens=max_tokens if max_tokens is not None else 2048,
        )
        if system_instruction.strip():
            config.system_instruction = system_instruction.strip()

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=config,
            )
            text_output = response.text or ""
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }

            return NormalizedChatResponse(
                content=text_output,
                model_name=self._model_name,
                token_usage=usage,
            )
        except Exception as exc:
            err_str = str(exc)
            logger.error(f"Gemini API error: {err_str}")
            # Automatic fallback to high-quota flash-lite if primary hits 429 daily preview quota
            if ("429" in err_str or "resource_exhausted" in err_str.lower()) and self._model_name != "gemini-2.5-flash-lite":
                try:
                    logger.info("Auto-switching to gemini-2.5-flash-lite due to quota limit on primary model...")
                    fallback_res = await self._client.aio.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=contents,
                        config=config,
                    )
                    return NormalizedChatResponse(
                        content=fallback_res.text or "",
                        model_name="gemini-2.5-flash-lite",
                        token_usage={},
                    )
                except Exception as fb_exc:
                    logger.error(f"Fallback model also encountered error: {fb_exc}")
            raise AIServiceException(f"Gemini service error: {str(exc)}")


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-embedding-001",
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        if not api_key or not api_key.strip():
            raise AIServiceException("Gemini API key is missing or empty.")
        self._api_key = api_key
        # If user passed text-embedding-004 which is unavailable in the v1beta GenAI SDK, fallback to gemini-embedding-001
        if model_name == "text-embedding-004":
            logger.info("Auto-upgrading Gemini embedding model from text-embedding-004 to gemini-embedding-001")
            self._model_name = "gemini-embedding-001"
        else:
            self._model_name = model_name
        self._client = genai.Client(api_key=api_key)
        self._dimension = GEMINI_EMBEDDING_DIMENSIONS.get(self._model_name, 3072)

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_query(self, text: str) -> List[float]:
        vectors = await self.embed_documents([text])
        return vectors[0]

    async def embed_documents(self, texts: List[str], batch_size: int = 25) -> List[List[float]]:
        """
        Embed document chunks in rate-limited batches with automatic exponential backoff.
        Handles Gemini Free Tier quota restrictions (100 RPM) resiliently.
        """
        if not texts:
            return []

        results: List[List[float]] = []
        max_batch_retries = 5
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            for attempt in range(max_batch_retries):
                try:
                    response = await self._client.aio.models.embed_content(
                        model=self._model_name,
                        contents=batch if len(batch) > 1 else batch[0],
                    )

                    if hasattr(response, "embeddings") and response.embeddings:
                        for emb in response.embeddings:
                            vec = list(emb.values)
                            results.append(vec)
                            self._dimension = len(vec)
                    elif hasattr(response, "embedding") and response.embedding:
                        vec = list(response.embedding.values)
                        results.append(vec)
                        self._dimension = len(vec)
                    else:
                        raise AIServiceException("Unexpected embedding format from Gemini.")

                    # Brief pause between batches to smoothly stay under 100 requests per minute
                    if i + batch_size < len(texts):
                        await asyncio.sleep(0.4)

                    break  # Success, proceed to next batch

                except Exception as exc:
                    err_msg = str(exc)
                    is_rate_limit = (
                        "429" in err_msg
                        or "resource_exhausted" in err_msg.lower()
                        or "quota" in err_msg.lower()
                    )

                    if is_rate_limit and attempt < max_batch_retries - 1:
                        # Extract suggested retry delay from error if available
                        wait_seconds = 20.0
                        retry_match = re.search(r"retry in (\d+\.?\d*)s", err_msg, re.IGNORECASE)
                        if retry_match:
                            try:
                                wait_seconds = max(5.0, float(retry_match.group(1)) + 1.0)
                            except Exception:
                                wait_seconds = 20.0 * (attempt + 1)
                        else:
                            wait_seconds = 20.0 * (attempt + 1)

                        logger.warning(
                            f"⚠️ [Gemini Rate Limit] 429 quota reached on batch {batch_num}/{total_batches}. "
                            f"Auto-waiting {wait_seconds:.1f}s before retry (attempt {attempt + 1}/{max_batch_retries})..."
                        )
                        await asyncio.sleep(wait_seconds)
                    else:
                        if "not found" in err_msg.lower() and "text-embedding-004" in err_msg.lower():
                            raise AIServiceException(
                                "Gemini model 'text-embedding-004' is not supported in the Google GenAI SDK. Please set GEMINI_EMBEDDING_MODEL=gemini-embedding-001 in your .env file.",
                                status_code=400,
                            )
                        if is_rate_limit:
                            raise AIServiceException(
                                "Gemini Free Tier rate limit reached. Retries exhausted.",
                                status_code=429,
                            )
                        logger.error(f"Gemini embedding error: {exc}")
                        raise AIServiceException(f"Failed to generate Gemini embeddings: {str(exc)}")

        return results

