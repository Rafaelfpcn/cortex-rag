from typing import List, Optional
from pydantic import BaseModel, Field

class Citation(BaseModel):
    document_id: str
    document_title: str
    chunk_index: int
    score: float
    snippet: str
    page: Optional[int] = 1

class ChatQueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    document_ids: Optional[List[str]] = None
    stream: bool = True

class ChatStreamChunk(BaseModel):
    type: str  # "delta", "citations", "cache_hit", "done", "error"
    delta: Optional[str] = None
    citations: Optional[List[Citation]] = None
    cache_hit: Optional[bool] = False
    similarity_score: Optional[float] = None
    latency_ms: Optional[float] = None

class SystemMetrics(BaseModel):
    total_queries: int
    cache_hits: int
    cache_hit_rate_pct: float
    avg_latency_ms: float
    total_documents: int
    total_chunks: int
