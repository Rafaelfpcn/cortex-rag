import pytest
from app.core.semantic_cache import SemanticCache, cosine_similarity

def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v2), 0.001) == 1.0

    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v3), 0.001) == 0.0

@pytest.mark.asyncio
async def test_semantic_cache_hit_and_miss():
    cache = SemanticCache()
    tenant = "tenant_test_1"

    query_vec = [0.5, 0.5, 0.5]
    await cache.set(
        tenant_id=tenant,
        query="Como funciona a política de segurança?",
        query_vector=query_vec,
        response="A política de segurança exige MFA.",
        citations=[{"doc": "doc1"}]
    )

    # Identical query vector should HIT
    hit = await cache.get(tenant, [0.5, 0.5, 0.5], threshold=0.90)
    assert hit is not None
    resp, citations, score = hit
    assert resp == "A política de segurança exige MFA."
    assert score > 0.99

    # Orthogonal query vector should MISS
    miss = await cache.get(tenant, [-0.5, 0.5, 0.0], threshold=0.90)
    assert miss is None
