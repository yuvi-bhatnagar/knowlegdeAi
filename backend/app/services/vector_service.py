import uuid
from typing import Any, Dict, List, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import settings
from app.core.exceptions import AIServiceException, EmbeddingDimensionMismatchException
from app.core.logging import logger


class VectorService:
    """Manages Qdrant vector collections, upserting chunks with metadata, and owner-scoped retrieval."""

    def __init__(self, client: Optional[AsyncQdrantClient] = None):
        if client:
            self.client = client
        else:
            self.client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                timeout=10.0,
            )

    @classmethod
    def get_collection_name(cls, model_name: str, dimension: int) -> str:
        """Create sanitized, versioned collection name combining prefix, model, and vector dimensions."""
        clean_model = model_name.replace("/", "_").replace("-", "_").replace(".", "_")
        return f"{settings.QDRANT_COLLECTION_PREFIX}_{clean_model}_{dimension}"

    async def ensure_collection(self, collection_name: str, vector_size: int) -> None:
        """Create collection if it does not exist; verify dimensionality if it does."""
        try:
            collections = await self.client.get_collections()
            existing_names = [col.name for col in collections.collections]

            if collection_name not in existing_names:
                logger.info(f"Creating Qdrant collection '{collection_name}' with dimension {vector_size}...")
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=vector_size,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
                # Create payload indexes on owner_id and document_id for fast filtered retrieval
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="owner_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="document_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
            else:
                info = await self.client.get_collection(collection_name)
                # Ensure vector dimension matches
                vectors_config = info.config.params.vectors
                actual_size = getattr(vectors_config, "size", None)
                if actual_size and actual_size != vector_size:
                    raise EmbeddingDimensionMismatchException(expected_dim=actual_size, actual_dim=vector_size)
        except EmbeddingDimensionMismatchException:
            raise
        except Exception as exc:
            logger.warning(f"Could not connect or configure Qdrant collection: {exc}")
            raise AIServiceException(f"Vector database error: {str(exc)}")

    async def upsert_chunks(
        self,
        collection_name: str,
        points: List[qmodels.PointStruct],
        batch_size: int = 100,
    ) -> None:
        """Upsert chunk points into Qdrant in safe, high-throughput batches."""
        if not points:
            return
        try:
            for i in range(0, len(points), batch_size):
                batch = points[i : i + batch_size]
                await self.client.upsert(
                    collection_name=collection_name,
                    points=batch,
                    wait=True,
                )
        except Exception as exc:
            logger.error(f"Failed to upsert points into Qdrant: {exc}")
            raise AIServiceException(f"Failed to index document chunks into vector database: {str(exc)}")

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        owner_id: uuid.UUID,
        document_ids: Optional[List[uuid.UUID]] = None,
        limit: int = 5,
        score_threshold: float = 0.60,
    ) -> List[qmodels.ScoredPoint]:
        """Perform cosine similarity search strictly constrained by owner_id and optional document_ids."""
        must_filters: List[qmodels.FieldCondition] = [
            qmodels.FieldCondition(
                key="owner_id",
                match=qmodels.MatchValue(value=str(owner_id)),
            )
        ]

        if document_ids:
            must_filters.append(
                qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchAny(any=[str(doc_id) for doc_id in document_ids]),
                )
            )

        query_filter = qmodels.Filter(must=must_filters)

        try:
            # AsyncQdrantClient in qdrant-client >= 1.10 uses query_points
            if hasattr(self.client, "query_points"):
                response = await self.client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    score_threshold=score_threshold,
                )
                return response.points
            elif hasattr(self.client, "search"):
                results = await self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    score_threshold=score_threshold,
                )
                return results
            else:
                raise AIServiceException("AsyncQdrantClient does not support query_points or search.")
        except Exception as exc:
            logger.error(f"Vector search failed in Qdrant: {exc}")
            raise AIServiceException(f"Vector search failed: {str(exc)}")

    async def delete_by_document(
        self,
        collection_name: str,
        document_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> None:
        """Remove all points belonging to a specific document and owner."""
        try:
            filter_to_delete = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=str(document_id))),
                    qmodels.FieldCondition(key="owner_id", match=qmodels.MatchValue(value=str(owner_id))),
                ]
            )
            await self.client.delete(
                collection_name=collection_name,
                points_selector=qmodels.FilterSelector(filter=filter_to_delete),
            )
        except Exception as exc:
            logger.warning(f"Could not delete vectors for document {document_id}: {exc}")

