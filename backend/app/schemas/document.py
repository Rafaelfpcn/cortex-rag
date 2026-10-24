from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chunk_index: int
    content: str
    meta: dict
    created_at: datetime

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    title: str
    file_name: str
    file_hash: str
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int

class UploadResponse(BaseModel):
    document_id: str
    file_name: str
    status: str
    message: str
