"""
Token-bucket rate limiter — built from scratch, Redis-backed.

Algorithm reference: Designing Data-Intensive Applications, Ch. 8
(reliability under partial failures — rate limiting as a system primitive).

How the token bucket works
──────────────────────────
Each caller (user ID or IP address) owns a conceptual "bucket":

  ┌─────────────────────────────────────────────────────────────────┐
  │  bucket.capacity     = N  (max tokens, i.e. burst ceiling)      │
  │  bucket.refill_rate  = N / window_seconds  (tokens per second)  │
  │  bucket.tokens       = current available tokens  (float)        │
  │  bucket.ts           = Unix timestamp of last read (float)      │
  └─────────────────────────────────────────────────────────────────┘

On each request:
  1. elapsed  = now − last_ts
  2. tokens   = min(capacity, stored_tokens + elapsed × refill_rate)
  3. If tokens ≥ cost → consume, allow.
     Else            → deny, return ceil(deficit / refill_rate) as Retry-After.

State is stored in a Redis hash.  All read-modify-write steps run inside
a single Lua script, which Redis executes atomically — no MULTI/EXEC
overhead, no race window between two concurrent requests.

Redis key schema
────────────────
  rate_limit:{key_prefix}:{identifier}  →  Hash { tokens: float, ts: float }

  TTL is set to 2 × window_seconds so idle buckets are collected automatically,
  and the next request after expiry receives a fresh full bucket.
"""

import time
from dataclasses import dataclass
from typing import Callable

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status
from typing import Annotated

from api.deps import get_current_user, get_redis
from models.user import User


# ── Lua script ────────────────────────────────────────────────────────────────
#
# KEYS[1]  →  Redis hash key for this bucket
# ARGV[1]  →  capacity       (int, max tokens)
# ARGV[2]  →  refill_rate    (float, tokens per second)
# ARGV[3]  →  now            (float, Unix timestamp with sub-second precision)
# ARGV[4]  →  cost           (int, tokens this request consumes; normally 1)
# ARGV[5]  →  ttl            (int, seconds until the key expires)
#
# Returns a three-element Lua table → Python list:
#   [0]  allowed       (1 = yes, 0 = no)
#   [1]  remaining     (floor of tokens left after this request)
#   [2]  retry_after   (seconds until 1 token refills; 0 when allowed)
#
# Lua 5.1 note (Redis embedded runtime):
#   math.ceil / math.floor return floats in Lua 5.1.
#   Redis converts Lua floats to Redis integers by truncation, so
#   we use  math.floor(x) + 1  as a safe ceiling to avoid any edge-case
#   truncation error.  All values passed to EXPIRE are pre-computed integers
#   from Python so the command never receives a fractional argument.

_BUCKET_SCRIPT = """
local key         = KEYS[1]
local capacity    = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now         = tonumber(ARGV[3])
local cost        = tonumber(ARGV[4])
local ttl         = tonumber(ARGV[5])

local state  = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(state[1])
local ts     = tonumber(state[2])

if tokens == nil then
    -- First request for this identifier: start with a full bucket then consume.
    tokens = capacity - cost
    if tokens < 0 then
        local retry_after = math.floor(cost / refill_rate) + 1
        return {0, 0, retry_after}
    end
    redis.call('HSET', key, 'tokens', tokens, 'ts', now)
    redis.call('EXPIRE', key, ttl)
    return {1, math.floor(tokens), 0}
end

-- Refill tokens proportionally to elapsed time (continuous drip model).
-- math.max guards against backward clock steps (NTP slew, container migration).
local elapsed = math.max(0, now - ts)
tokens = math.min(capacity, tokens + elapsed * refill_rate)

local allowed
local retry_after = 0

if tokens >= cost then
    tokens  = tokens - cost
    allowed = 1
else
    -- Ceiling without relying on math.ceil returning an integer in Lua 5.1.
    local deficit  = cost - tokens
    retry_after    = math.floor(deficit / refill_rate) + 1
    allowed        = 0
end

redis.call('HSET', key, 'tokens', tokens, 'ts', now)
redis.call('EXPIRE', key, ttl)

return {allowed, math.floor(tokens), retry_after}
"""


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BucketResult:
    allowed: bool
    remaining: int   # whole tokens left after this request
    retry_after: int  # seconds until next token is available; 0 when allowed


# ── Core class ────────────────────────────────────────────────────────────────

class TokenBucketLimiter:
    """
    Stateless Python object.  All mutable state lives in Redis.

    Parameters
    ──────────
    capacity        Max tokens a bucket can hold (also the burst ceiling).
    window_seconds  Time to refill an empty bucket to full capacity.
    key_prefix      Namespaces the Redis key (e.g. "booking", "register").
    """

    def __init__(self, capacity: int, window_seconds: int, key_prefix: str) -> None:
        if capacity <= 0 or window_seconds <= 0:
            raise ValueError("capacity and window_seconds must be positive integers")
        self.capacity = capacity
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix
        self._refill_rate: float = capacity / window_seconds   # tokens / second
        self._ttl: int = window_seconds * 2                    # Redis key TTL

    # ── Core check ───────────────────────────────────────────────────────────

    async def check(
        self,
        redis: aioredis.Redis,
        identifier: str,
        cost: int = 1,
    ) -> BucketResult:
        """
        Atomically consume `cost` tokens for `identifier`.
        Returns a BucketResult indicating whether the request is allowed.
        """
        key = f"rate_limit:{self.key_prefix}:{identifier}"
        raw = await redis.eval(
            _BUCKET_SCRIPT,
            1,                          # numkeys
            key,                        # KEYS[1]
            str(self.capacity),         # ARGV[1]
            str(self._refill_rate),     # ARGV[2]
            str(time.time()),           # ARGV[3]
            str(cost),                  # ARGV[4]
            str(self._ttl),             # ARGV[5]
        )
        allowed, remaining, retry_after = raw
        return BucketResult(
            allowed=bool(allowed),
            remaining=int(remaining),
            retry_after=int(retry_after),
        )

    # ── 429 response helper ───────────────────────────────────────────────────

    def _raise_429(self, result: BucketResult) -> None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded — {self.capacity} requests per "
                   f"{self.window_seconds}s. Retry in {result.retry_after}s.",
            headers={
                "Retry-After":          str(result.retry_after),
                "X-RateLimit-Limit":    str(self.capacity),
                "X-RateLimit-Window":   str(self.window_seconds),
                "X-RateLimit-Remaining": "0",
            },
        )

    # ── Dependency factories ──────────────────────────────────────────────────
    # Call each factory once at module level and store the result.
    # FastAPI uses the function-object identity for dependency caching,
    # so a stable reference ensures get_current_user is called only once
    # even when both the route and the rate limiter depend on it.

    def limit_by_user(self) -> Callable:
        """
        FastAPI dependency: enforces the limit per authenticated user ID.
        Auth is checked first (prerequisite in the dependency graph), so
        unauthenticated requests still get 401, not 429.
        """
        limiter = self

        async def _dep(
            redis: Annotated[aioredis.Redis, Depends(get_redis)],
            current_user: Annotated[User, Depends(get_current_user)],
        ) -> None:
            result = await limiter.check(redis, str(current_user.id))
            if not result.allowed:
                limiter._raise_429(result)

        return _dep

    def limit_by_ip(self) -> Callable:
        """
        FastAPI dependency: enforces the limit per client IP address.
        Reads X-Forwarded-For when the app is behind Nginx (already wired).
        No auth required — suitable for public endpoints like /register.
        """
        limiter = self

        async def _dep(
            request: Request,
            redis: Annotated[aioredis.Redis, Depends(get_redis)],
        ) -> None:
            forwarded = request.headers.get("X-Forwarded-For")
            ip = forwarded.split(",")[0].strip() if forwarded else (
                request.client.host or "unknown"
            )
            result = await limiter.check(redis, ip)
            if not result.allowed:
                limiter._raise_429(result)

        return _dep
