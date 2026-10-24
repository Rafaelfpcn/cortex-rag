from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
from app.core.logging import logger

# Check if using PostgreSQL with pgvector or SQLite
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if is_sqlite else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def init_db():
    """Initializes tables and seeds default demo data if needed."""
    async with engine.begin() as conn:
        # If postgres, enable pgvector extension
        if not is_sqlite:
            try:
                from sqlalchemy import text
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("pgvector extension verified/enabled.")
            except Exception as e:
                logger.warning(f"Could not initialize pgvector extension: {e}")

        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully.")
