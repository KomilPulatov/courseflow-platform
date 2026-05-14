from dataclasses import dataclass
from time import time

from fastapi import HTTPException, status
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.metrics import record_redis_operation
from app.modules.platform.redis_client import get_redis_client


@dataclass
class TokenBucket:
    capacity: int
    refill_rate_per_second: float
    tokens: float
    last_refill_at: float

    @classmethod
    def full(cls, *, capacity: int, refill_rate_per_second: float) -> "TokenBucket":
        return cls(
            capacity=capacity,
            refill_rate_per_second=refill_rate_per_second,
            tokens=float(capacity),
            last_refill_at=time(),
        )

    def allow(self, *, cost: int = 1, now: float | None = None) -> bool:
        current_time = now if now is not None else time()
        elapsed = max(current_time - self.last_refill_at, 0)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate_per_second)
        self.last_refill_at = current_time
        if self.tokens < cost:
            return False
        self.tokens -= cost
        return True


class RedisTokenBucketLimiter:
    """Redis-backed token bucket shared by all backend containers."""

    _ALLOW_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill_at')
local tokens = tonumber(bucket[1]) or capacity
local last_refill_at = tonumber(bucket[2]) or now
local elapsed = math.max(now - last_refill_at, 0)
tokens = math.min(capacity, tokens + (elapsed * refill))

if tokens < cost then
  redis.call('HSET', key, 'tokens', tokens, 'last_refill_at', now)
  redis.call('EXPIRE', key, 120)
  return 0
end

redis.call('HSET', key, 'tokens', tokens - cost, 'last_refill_at', now)
redis.call('EXPIRE', key, 120)
return 1
"""

    def __init__(self, key_prefix: str, capacity: int, refill_per_second: float) -> None:
        self.key_prefix = key_prefix
        self.capacity = capacity
        self.refill_per_second = refill_per_second

    def allow(self, subject: str, cost: float = 1.0) -> bool:
        client = get_redis_client()
        if client is None:
            return True

        key = f"{self.key_prefix}:{subject}"
        now = time()
        try:
            allowed = bool(
                client.eval(
                    self._ALLOW_SCRIPT,
                    1,
                    key,
                    self.capacity,
                    self.refill_per_second,
                    cost,
                    now,
                )
            )
            record_redis_operation("rate_limit", "allowed" if allowed else "blocked")
            return allowed
        except RedisError:
            # We prefer a temporary fail-open behavior over blocking registration entirely.
            record_redis_operation("rate_limit", "error")
            return True


def enforce_registration_rate_limit(student_id: int) -> None:
    if not settings.REGISTRATION_RATE_LIMIT_ENABLED:
        return

    per_minute = max(1, settings.REGISTRATION_RATE_LIMIT_PER_MINUTE)
    limiter = RedisTokenBucketLimiter(
        key_prefix="registration:rate-limit",
        capacity=per_minute,
        refill_per_second=per_minute / 60,
    )
    if not limiter.allow(str(student_id)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration requests. Please wait and try again.",
        )
