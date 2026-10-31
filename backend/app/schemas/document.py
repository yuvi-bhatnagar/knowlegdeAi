import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size: int
    checksum: str
    status: str
    error_summary: Optional[str] = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    status: str
    message: str


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    chunk_count: int
    error_summary: Optional[str] = None
