from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import DocumentChunk, Document
from app.core.semantic_cache import cosine_similarity
from app.config import settings

class HybridSearchEngine:
    """
    Hybrid Search Engine combining:
    1. Dense Vector Search (semantic similarity)
    2. Lexical / Keyword Search (exact token matching)
    Combined using Reciprocal Rank Fusion (RRF, k=60).
    """
    def __init__(self, k_rrf: int = 60):
        self.k_rrf = k_rrf

    async def search(
        self,
        db: AsyncSession,
        tenant_id: str,
        query_text: str,
        query_vector: List[float],
        document_ids: Optional[List[str]] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        k = top_k or settings.TOP_K_RETRIEVAL

        # 1. Fetch chunks for the tenant (and optional document filters)
        stmt = (
            select(DocumentChunk, Document.title)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                DocumentChunk.tenant_id == tenant_id,
                Document.status == "INDEXED"
            )
        )
        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

        result = await db.execute(stmt)
        rows = result.all()

        if not rows:
            return []

        # 2. Score Dense
        dense_scores = []
        for chunk, doc_title in rows:
            sim = cosine_similarity(query_vector, chunk.embedding)
            dense_scores.append((chunk, doc_title, sim))
        dense_ranked = sorted(dense_scores, key=lambda x: x[2], reverse=True)

        # 3. Score Lexical (BM25-style term frequency)
        query_terms = set(query_text.lower().split())
        lexical_scores = []
        for chunk, doc_title in rows:
            content_lower = chunk.content.lower()
            term_matches = sum(1 for term in query_terms if term in content_lower)
            # Normalize by content length
            lex_score = term_matches / (1 + len(chunk.content.split()))
            lexical_scores.append((chunk, doc_title, lex_score))
        lexical_ranked = sorted(lexical_scores, key=lambda x: x[2], reverse=True)

        # 4. Reciprocal Rank Fusion (RRF)
        # rrf_score = 1 / (k + rank_dense) + 1 / (k + rank_lexical)
        rrf_map: Dict[str, Dict[str, Any]] = {}

        for rank, (chunk, doc_title, score) in enumerate(dense_ranked):
            c_id = chunk.id
            if c_id not in rrf_map:
                rrf_map[c_id] = {
                    "chunk": chunk,
                    "doc_title": doc_title,
                    "dense_score": score,
                    "lexical_score": 0.0,
                    "rrf_score": 0.0
                }
            rrf_map[c_id]["rrf_score"] += 1.0 / (self.k_rrf + rank + 1)

        for rank, (chunk, doc_title, score) in enumerate(lexical_ranked):
            c_id = chunk.id
            if c_id in rrf_map:
                rrf_map[c_id]["lexical_score"] = score
                rrf_map[c_id]["rrf_score"] += 1.0 / (self.k_rrf + rank + 1)

        # Sort by final RRF score
        fused = sorted(rrf_map.values(), key=lambda x: x["rrf_score"], reverse=True)

        # Format output
        top_results = []
        for item in fused[:k]:
            c = item["chunk"]
            top_results.append({
                "chunk_id": c.id,
                "document_id": c.document_id,
                "document_title": item["doc_title"],
                "chunk_index": c.chunk_index,
                "content": c.content,
                "metadata": c.meta,
                "dense_score": round(item["dense_score"], 4),
                "lexical_score": round(item["lexical_score"], 4),
                "rrf_score": round(item["rrf_score"], 5),
            })

        return top_results

hybrid_search = HybridSearchEngine()
