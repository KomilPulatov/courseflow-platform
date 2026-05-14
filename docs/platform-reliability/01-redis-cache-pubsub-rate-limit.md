# Redis Cache, Pub/Sub, And Rate Limit

## File Locations

- `backend/app/core/config.py`
- `backend/app/modules/platform/redis_client.py`
- `backend/app/modules/platform/rate_limiter.py`
- `backend/app/modules/registration/availability.py`
- `backend/app/modules/registration/publishers.py`
- `backend/app/api/v1/endpoints/sections.py`
- `backend/app/api/deps.py`
- `docker-compose.yml`

## What Redis Does

Redis has three separate jobs in this project:

1. Cache section availability for a short time.
2. Publish section availability changes to all backend replicas.
3. Store rate-limit token buckets shared by all backend replicas.

This is useful because the project runs two backend containers behind Nginx. In-memory state would only
exist inside one container. Redis gives both containers a shared place to coordinate.

## Redis Configuration

`backend/app/core/config.py` adds these settings:

```python
REDIS_URL: str = "redis://localhost:6379/0"
REDIS_ENABLED: bool = False
REDIS_CACHE_TTL_SECONDS: int = 30
REGISTRATION_RATE_LIMIT_ENABLED: bool = False
REGISTRATION_RATE_LIMIT_PER_MINUTE: int = 60
```

The defaults are disabled so normal unit tests do not require Redis. `docker-compose.yml` enables them
for the full platform demo.

## Shared Redis Client

`backend/app/modules/platform/redis_client.py` contains:

```python
@lru_cache(maxsize=1)
def get_redis_client() -> Redis | None:
```

This returns one reusable Redis client when Redis is enabled. Returning `None` when disabled keeps local
development and unit tests simple.

## Availability Cache

`backend/app/modules/registration/availability.py` defines a stable key:

```python
def section_availability_cache_key(section_id: int) -> str:
    return f"section:{section_id}:availability"
```

The read path is:

```python
get_cached_or_calculated_availability(db, section_id)
```

It tries Redis first. On a cache hit, it returns the stored `SectionAvailability`. On a miss or Redis
error, it calculates from PostgreSQL and writes a fresh cache value.

## Availability Pub/Sub

After registration or waitlist changes, `RedisAvailabilityPublisher` recalculates availability from the
database and publishes a Redis message:

```python
availability = calculate_section_availability(self.db, section_id)
cache_section_availability(availability)
publish_section_availability(availability)
```

The important detail is that it calculates fresh data after the database commit. That avoids publishing
old cached values.

## Distributed Rate Limit

`RedisTokenBucketLimiter` stores tokens in a Redis hash and updates it with one Lua script:

```python
client.eval(self._ALLOW_SCRIPT, 1, key, self.capacity, self.refill_per_second, cost, now)
```

The registration route uses:

```python
get_rate_limited_current_student_id(...)
```

That dependency first identifies the student, then calls `enforce_registration_rate_limit(student_id)`.
Because the bucket lives in Redis, the limit is shared across `backend-1` and `backend-2`. The Lua
script makes the token check and token update atomic, so two backend replicas cannot both spend the same
token at the same time.

## Failure Behavior

Redis failures are handled as fail-open for registration. That means Redis problems do not block students
from registering. The system logs and records metrics for Redis errors, then falls back to database reads
or allows the request.
