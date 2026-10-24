import hashlib
import json
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document, DocumentChunk
from app.services.chunking_service import chunker
from app.services.embedding_service import embedding_service
from app.core.logging import logger

class IngestionService:
    """
    Asynchronous document ingestion processor.
    Performs SHA-256 idempotency check, text extraction, recursive chunking,
    batch embedding generation, and atomic persistence.
    """
    async def process_document(
        self,
        db: AsyncSession,
        tenant_id: str,
        title: str,
        file_name: str,
        content: str
    ) -> Tuple[Document, bool]:
        """
        Returns:
            (Document, is_duplicate: bool)
        """
        # 1. Compute SHA-256 for idempotency
        file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Check existing
        existing_doc_stmt = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.file_hash == file_hash
        )
        result = await db.execute(existing_doc_stmt)
        existing_doc = result.scalar_one_or_none()

        if existing_doc and existing_doc.status == "INDEXED":
            logger.info(f"Idempotency hit: Document '{title}' with hash {file_hash[:8]} already indexed.")
            return existing_doc, True

        # Create or update document
        doc = Document(
            tenant_id=tenant_id,
            title=title,
            file_name=file_name,
            file_hash=file_hash,
            status="PROCESSING",
            chunk_count=0
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        try:
            # 2. Chunking
            chunks_data = chunker.split_text(content)
            if not chunks_data:
                doc.status = "INDEXED"
                await db.commit()
                return doc, False

            texts = [c["content"] for c in chunks_data]

            # 3. Batch Embeddings
            embeddings = await embedding_service.get_embeddings(texts)

            # 4. Persistence
            for c_info, emb in zip(chunks_data, embeddings):
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    tenant_id=tenant_id,
                    chunk_index=c_info["chunk_index"],
                    content=c_info["content"],
                    metadata_json=json.dumps(c_info["metadata"]),
                    embedding_json=json.dumps(emb)
                )
                db.add(chunk_record)

            doc.chunk_count = len(chunks_data)
            doc.status = "INDEXED"
            await db.commit()
            await db.refresh(doc)
            logger.info(f"Successfully indexed document '{title}' with {doc.chunk_count} chunks.")
            return doc, False

        except Exception as e:
            logger.error(f"Failed to ingest document '{title}': {e}", exc_info=True)
            doc.status = "FAILED"
            doc.error_message = str(e)
            await db.commit()
            raise e

ingestion_service = IngestionService()
