import pytest
import asyncio
from app.core.rate_limiter import TokenBucketRateLimiter

@pytest.mark.asyncio
async def test_token_bucket_rate_limiter_burst():
    limiter = TokenBucketRateLimiter()
    ident = "test_user_burst"

    # Consume up to capacity of 3
    for i in range(3):
        allowed, remaining, wait = await limiter.check_rate_limit(ident, cost=1, capacity=3, refill_rate_per_sec=1.0)
        assert allowed is True
        assert remaining == 2 - i

    # Exceed capacity
    allowed, remaining, wait = await limiter.check_rate_limit(ident, cost=1, capacity=3, refill_rate_per_sec=1.0)
    assert allowed is False
    assert wait >= 1

@pytest.mark.asyncio
async def test_token_bucket_refill():
    limiter = TokenBucketRateLimiter()
    ident = "test_user_refill"

    # Drain bucket
    allowed, _, _ = await limiter.check_rate_limit(ident, cost=2, capacity=2, refill_rate_per_sec=2.0)
    assert allowed is True

    # Immediate request should fail
    allowed, _, _ = await limiter.check_rate_limit(ident, cost=1, capacity=2, refill_rate_per_sec=2.0)
    assert allowed is False

    # Wait for refill (0.6s should refill >= 1 token with rate of 2 tokens/sec)
    await asyncio.sleep(0.6)
    allowed, remaining, _ = await limiter.check_rate_limit(ident, cost=1, capacity=2, refill_rate_per_sec=2.0)
    assert allowed is True
