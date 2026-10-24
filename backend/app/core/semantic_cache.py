import math
import time
from typing import List, Optional, Tuple, Dict, Any
from app.config import settings
from app.core.logging import logger

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

class SemanticCache:
    """
    Semantic Cache for LLM and RAG responses.
    Caches queries by embedding vector to avoid costly re-inference when
    semantically identical or very close queries are made.
    """
    def __init__(self):
        # In-memory store: tenant_id -> list of cache entries
        # entry: {"query": str, "vector": list[float], "response": str, "citations": list, "timestamp": float}
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    async def get(
        self,
        tenant_id: str,
        query_vector: List[float],
        threshold: Optional[float] = None
    ) -> Optional[Tuple[str, List[Dict[str, Any]], float]]:
        """
        Lookup semantic cache.
        Returns:
            (cached_response, cached_citations, similarity_score) if hit, else None
        """
        min_thresh = threshold or settings.SEMANTIC_CACHE_THRESHOLD
        tenant_entries = self._cache.get(tenant_id, [])

        best_score = -1.0
        best_entry = None

        for entry in tenant_entries:
            sim = cosine_similarity(query_vector, entry["vector"])
            if sim > best_score:
                best_score = sim
                best_entry = entry

        if best_entry and best_score >= min_thresh:
            logger.info(f"Semantic Cache HIT (Score: {best_score:.4f} >= {min_thresh}) for tenant {tenant_id}")
            return best_entry["response"], best_entry["citations"], best_score

        return None

    async def set(
        self,
        tenant_id: str,
        query: str,
        query_vector: List[float],
        response: str,
        citations: List[Dict[str, Any]],
        ttl_seconds: int = 86400
    ) -> None:
        """Store query vector and its generated response into the semantic cache."""
        if tenant_id not in self._cache:
            self._cache[tenant_id] = []

        entry = {
            "query": query,
            "vector": query_vector,
            "response": response,
            "citations": citations,
            "created_at": time.time(),
        }

        # Keep cache bounded (LRU style / cap at 1000 items per tenant)
        if len(self._cache[tenant_id]) >= 1000:
            self._cache[tenant_id].pop(0)

        self._cache[tenant_id].append(entry)

semantic_cache = SemanticCache()
