import time
import asyncio
from typing import Tuple, Optional
import redis.asyncio as aioredis
from app.config import settings
from app.core.logging import logger

class TokenBucketRateLimiter:
    """
    Distributed Token Bucket Rate Limiter with Redis support and
    in-memory fallback for local development and offline resilience.
    """
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self._memory_buckets: dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self._redis_attempted = False

    async def _get_redis(self) -> Optional[aioredis.Redis]:
        if not self._redis_attempted and settings.REDIS_URL:
            self._redis_attempted = True
            try:
                client = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=1.0)
                await client.ping()
                self.redis_client = client
                logger.info("Rate limiter connected to distributed Redis cluster.")
            except Exception as e:
                logger.warning(f"Redis unavailable for RateLimiter ({e}), falling back to in-memory bucket.")
                self.redis_client = None
        return self.redis_client

    async def check_rate_limit(
        self,
        identifier: str,
        cost: int = 1,
        capacity: Optional[int] = None,
        refill_rate_per_sec: Optional[float] = None
    ) -> Tuple[bool, int, int]:
        """
        Returns:
            (allowed: bool, remaining_tokens: int, retry_after_sec: int)
        """
        cap = capacity or settings.RATE_LIMIT_BURST_CAPACITY
        refill_rate = refill_rate_per_sec or (settings.RATE_LIMIT_TOKENS_PER_MINUTE / 60.0)
        
        client = await self._get_redis()
        now = time.time()

        if client:
            try:
                key = f"ratelimit:{identifier}"
                # Lua script for atomic Token Bucket in Redis
                lua_script = """
                local key = KEYS[1]
                local now = tonumber(ARGV[1])
                local cap = tonumber(ARGV[2])
                local rate = tonumber(ARGV[3])
                local cost = tonumber(ARGV[4])
                
                local bucket = redis.call('HMGET', key, 'tokens', 'last_updated')
                local tokens = tonumber(bucket[1])
                local last_updated = tonumber(bucket[2])
                
                if not tokens then
                    tokens = cap
                    last_updated = now
                else
                    local delta = math.max(0, now - last_updated)
                    tokens = math.min(cap, tokens + (delta * rate))
                    last_updated = now
                end
                
                if tokens >= cost then
                    tokens = tokens - cost
                    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)
                    redis.call('EXPIRE', key, math.ceil(cap / rate))
                    return {1, math.floor(tokens), 0}
                else
                    local missing = cost - tokens
                    local wait_time = math.ceil(missing / rate)
                    return {0, math.floor(tokens), wait_time}
                end
                """
                res = await client.eval(lua_script, 1, key, now, cap, refill_rate, cost)
                allowed = bool(res[0])
                remaining = int(res[1])
                retry_after = int(res[2])
                return allowed, remaining, retry_after
            except Exception as e:
                logger.warning(f"Redis rate limit check failed: {e}. Using in-memory fallback.")

        # In-memory fallback
        async with self._lock:
            bucket = self._memory_buckets.get(identifier)
            if not bucket:
                tokens = float(cap)
                last_updated = now
            else:
                tokens = bucket["tokens"]
                last_updated = bucket["last_updated"]
                delta = max(0.0, now - last_updated)
                tokens = min(float(cap), tokens + (delta * refill_rate))

            if tokens >= cost:
                tokens -= cost
                self._memory_buckets[identifier] = {
                    "tokens": tokens,
                    "last_updated": now
                }
                return True, int(tokens), 0
            else:
                missing = cost - tokens
                wait_time = int(missing / refill_rate) + 1
                return False, int(tokens), wait_time

rate_limiter = TokenBucketRateLimiter()
