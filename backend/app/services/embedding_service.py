import math
import hashlib
from typing import List
import httpx
from app.config import settings
from app.core.logging import logger

class EmbeddingService:
    """
    Embedding service supporting both OpenAI text-embedding-3-small and
    a high-speed deterministic local subword projection generator (384-dim).
    Guarantees zero-failure operation even without external API keys.
    """
    def __init__(self):
        self.dimension = settings.EMBEDDING_DIMENSION

    async def get_embedding(self, text: str) -> List[float]:
        if settings.OPENAI_API_KEY:
            try:
                return await self._get_openai_embedding(text)
            except Exception as e:
                logger.warning(f"OpenAI embedding call failed ({e}), falling back to deterministic local model.")
        return self._get_local_embedding(text)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Batch generation
        return [await self.get_embedding(t) for t in texts]

    async def _get_openai_embedding(self, text: str) -> List[float]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"input": text, "model": "text-embedding-3-small"}
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]

    def _get_local_embedding(self, text: str) -> List[float]:
        """
        Fast, deterministic feature-hashing embedding vector of dimension 384,
        unit-normalized so cosine similarity works as expected.
        """
        vector = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            return vector

        for word in words:
            # 3-gram feature hashing
            for i in range(max(1, len(word) - 2)):
                gram = word[i:i+3]
                h = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dimension
                sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
                vector[idx] += sign

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

embedding_service = EmbeddingService()
