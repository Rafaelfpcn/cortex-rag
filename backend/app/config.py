import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "CortexRAG"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & Auth
    SECRET_KEY: str = "cortexrag-enterprise-secret-key-replace-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    # Default to async SQLite for friction-free local execution; set postgresql+asyncpg for production
    DATABASE_URL: str = "sqlite+aiosqlite:///./cortexrag.db"
    
    # Cache & Queues (Redis)
    REDIS_URL: Optional[str] = None  # e.g., redis://localhost:6379/0

    # Rate Limiting (Token Bucket)
    RATE_LIMIT_TOKENS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST_CAPACITY: int = 10

    # RAG & Semantic Cache
    EMBEDDING_DIMENSION: int = 384
    SEMANTIC_CACHE_THRESHOLD: float = 0.94  # Cosine similarity threshold for cache hit
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 4

    # AI Model Providers (Optional, fallback to high-fidelity mock if not set)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"

settings = Settings()
