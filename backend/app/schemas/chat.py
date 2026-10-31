import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: uuid.UUID
    filename: str
    page_number: Optional[int] = None
    chunk_index: int
    excerpt: str
    score: Optional[float] = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000, description="User's query")
    conversation_id: Optional[uuid.UUID] = Field(None, description="Existing conversation ID; if null, a new one is created")
    document_ids: Optional[List[uuid.UUID]] = Field(None, description="Optional document ID filters")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Override top-k results")


class ChatResponse(BaseModel):
    answer: str
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    citations: List[Citation] = Field(default_factory=list)
    model_used: str
    insufficient_evidence: bool = False
