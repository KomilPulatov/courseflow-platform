# 06 — Polyglot Persistence

## 1. Why CRSP needs Redis

PostgreSQL is excellent for relational, transactional data. However, CRSP also needs temporary, high-speed, low-latency data patterns:

- idempotency keys;
- rate-limit counters;
- section availability cache;
- WebSocket pub/sub across backend replicas;
- temporary seat holds if implemented;
- timetable-suggestion cache;
- short-lived INS sync status.

Redis fits these use cases better than relational tables because it supports TTL, atomic counters, fast key-value reads, and pub/sub.

## 2. Redis is not source of truth

Important rule:

> Redis improves speed, but PostgreSQL decides final registration state.

If Redis loses data, final enrollment is still correct.

## 3. Redis key design

```text
crsp:idempotency:{student_id}:{key}
crsp:rate-limit:{user_id}:{route}
crsp:section:{section_id}:availability
crsp:course-catalog:{semester_id}:{hash_of_filters}
crsp:ws:section:{section_id}
crsp:ins-sync:{student_id}:status
crsp:timetable-suggestion:{run_id}
```

## 4. Use case 1 — Idempotency

Problem:

A student may click “Register” twice or retry after network failure.

Redis solution:

```text
Key: crsp:idempotency:2310204:uuid
TTL: 24 hours
Value: previous response JSON
```

Behavior:

- first request processes normally;
- duplicate request returns saved result;
- prevents accidental duplicate side effects.

## 5. Use case 2 — Rate limiting

The from-scratch token-bucket component stores bucket state in Redis.

```text
Key: crsp:rate-limit:2310204:/registrations
Value:
{
  "tokens": 7,
  "last_refill_at": "..."
}
```

This works across two backend replicas because both replicas share Redis.

## 6. Use case 3 — Section availability cache

Course browsing is read-heavy.

```text
Key: crsp:section:101:availability
Value:
{
  "capacity": 30,
  "enrolled": 26,
  "remaining": 4,
  "waitlist_count": 8
}
TTL: 30–60 seconds
```

After register/drop/waitlist promotion, invalidate or update the key.

## 7. Use case 4 — WebSocket pub/sub

If Nginx load-balances WebSocket connections across backend replicas, backend-1 may process registration while some clients are connected to backend-2.

Redis pub/sub solves this:

```text
Channel: crsp:ws:section:101
Message: section.availability.updated
```

Every backend replica subscribes and forwards updates to its own connected clients.

## 8. Use case 5 — INS sync status

When INS sync runs in background:

```text
Key: crsp:ins-sync:2310204:status
Value:
{
  "status": "running",
  "started_at": "...",
  "source": "IUT_INS"
}
TTL: 10 minutes
```

Frontend can show:

```text
Syncing academic profile...
```

## 9. Use case 6 — Timetable suggestion cache

Timetable suggestion may be expensive.

```text
Key: crsp:timetable-suggestion:88
Value: generated options JSON
TTL: 1 hour
```

Final approved schedule is stored in PostgreSQL.

## 10. Failure policy

| Redis feature | If Redis is down |
|---|---|
| Course catalog cache | Read from PostgreSQL. |
| Availability cache | Recalculate from PostgreSQL. |
| Idempotency | Either use PostgreSQL fallback or return 503 for registration endpoint. |
| Rate limiting | Recommended: fail open for browsing, fail closed or stricter for registration. |
| WebSocket pub/sub | Registration still works; live updates may be delayed. |
| Timetable suggestion cache | Recompute or read from PostgreSQL result table. |

## 11. Measurement plan

Measure before/after:

| Query | Without Redis | With Redis | Target |
|---|---:|---:|---:|
| List courses | TBD ms | TBD ms | < 200 ms |
| Section availability | TBD ms | TBD ms | < 50 ms |
| Eligibility preview | TBD ms | TBD ms | < 250 ms |
| Timetable suggestion result read | TBD ms | TBD ms | < 100 ms |

Commands:

```bash
EXPLAIN ANALYZE SELECT ...
k6 run tests/load/catalog.js
k6 run tests/load/availability.js
```

## 12. Report paragraph

Use this in the report:

> CRSP uses PostgreSQL for relational and transactional state, while Redis is integrated as a key-value store for temporary and low-latency data. Redis stores idempotency keys, rate-limit buckets, section availability cache, WebSocket pub/sub messages, INS sync status, and timetable suggestion cache. This is a suitable polyglot persistence choice because these data items require TTL, atomic counters, fast reads, or pub/sub semantics, which are not natural fits for ordinary relational tables.
