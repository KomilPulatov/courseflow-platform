# 02 — Architecture

## 1. Architecture style

CRSP uses a **Dockerized modular monolith with supporting services**.

This is the best fit because:

- the business logic is tightly connected;
- consistency matters more than independent microservice deployment;
- the team has limited time;
- the project still needs multi-service orchestration;
- backend replicas, workers, Redis, RabbitMQ, and observability services satisfy distributed-system requirements.

## 2. High-level architecture

```mermaid
flowchart TD
    User[Browser] --> Nginx[Nginx Gateway]

    Nginx --> Frontend[Frontend]
    Nginx --> API1[FastAPI Backend Replica 1]
    Nginx --> API2[FastAPI Backend Replica 2]

    API1 --> PG[(PostgreSQL)]
    API2 --> PG

    API1 --> Redis[(Redis)]
    API2 --> Redis

    API1 --> Rabbit[RabbitMQ]
    API2 --> Rabbit
    Rabbit --> Worker[Celery Worker]

    API1 --> INS[IUT INS Connector]
    API2 --> INS
    Worker --> INS

    Worker --> PG
    Worker --> Redis

    API1 --> Otel[OpenTelemetry Collector]
    API2 --> Otel
    Worker --> Otel

    Otel --> Obs[Grafana/Prometheus/Loki/Tempo or SigNoz]
```

## 3. Data ownership

| Data | Source of truth |
|---|---|
| CRSP users | PostgreSQL |
| Student ID uniqueness | PostgreSQL |
| INS-verified academic data | INS, cached/snapshotted in PostgreSQL |
| Manual academic data | PostgreSQL, marked unverified |
| Course offerings | PostgreSQL |
| Rooms/time slots | PostgreSQL |
| Registration/enrollment | PostgreSQL |
| Waitlist | PostgreSQL |
| Temporary idempotency/rate-limit/cache | Redis |
| Live update pub/sub | Redis |
| Background event transport | RabbitMQ |

## 4. Main backend modules

```text
backend/app/
├─ main.py
├─ api/v1/
│  ├─ auth.py
│  ├─ student_profiles.py
│  ├─ professors.py
│  ├─ admin.py
│  ├─ courses.py
│  ├─ rooms.py
│  ├─ scheduling.py
│  ├─ registrations.py
│  ├─ waitlists.py
│  └─ websocket.py
├─ core/
│  ├─ config.py
│  ├─ security.py
│  ├─ exceptions.py
│  ├─ logging.py
│  └─ telemetry.py
├─ db/
│  ├─ base.py
│  ├─ session.py
│  └─ transaction.py
├─ modules/
│  ├─ auth/
│  ├─ student_profiles/
│  ├─ ins_integration/
│  ├─ professors/
│  ├─ courses/
│  ├─ rooms/
│  ├─ scheduling/
│  ├─ registration/
│  ├─ waitlist/
│  ├─ notifications/
│  └─ audit/
├─ integrations/
│  ├─ redis_client.py
│  ├─ rabbitmq.py
│  ├─ ins_client.py
│  └─ websocket_manager.py
└─ system_components/
   └─ token_bucket/
```

## 5. Request flows

### 5.1 INS-verified student onboarding

```mermaid
sequenceDiagram
    participant S as Student
    participant API as FastAPI
    participant INS as IUT INS
    participant DB as PostgreSQL
    participant MQ as RabbitMQ

    S->>API: POST /auth/student/ins-login
    API->>INS: Verify credentials
    INS-->>API: Student academic data
    API->>DB: Upsert user/student/profile
    API->>DB: Upsert completed courses and GPA snapshot
    API->>MQ: Publish StudentProfileSynced
    API-->>S: JWT + profile source ins_verified
```

### 5.2 Manual student onboarding

```mermaid
sequenceDiagram
    participant S as Student
    participant API as FastAPI
    participant DB as PostgreSQL

    S->>API: POST /student-profiles/manual
    API->>DB: Check unique student_id
    API->>DB: Save department/major/year/completed courses
    API-->>S: JWT/profile source manual
```

### 5.3 Professor room choice

```mermaid
sequenceDiagram
    participant P as Professor
    participant API as FastAPI
    participant DB as PostgreSQL
    participant MQ as RabbitMQ

    P->>API: GET /professor/room-options
    API->>DB: Load assigned sections and allocated rooms
    API-->>P: Allowed room options
    P->>API: POST /professor/room-preferences
    API->>DB: Validate room pool/capacity/conflict
    API->>DB: Save preference/selection
    API->>MQ: Publish ProfessorRoomSelected
    API-->>P: Confirmed
```

### 5.4 Registration

```mermaid
sequenceDiagram
    participant S as Student
    participant N as Nginx
    participant API as FastAPI
    participant R as Redis
    participant DB as PostgreSQL
    participant MQ as RabbitMQ
    participant WS as WebSocket

    S->>N: POST /api/v1/registrations
    N->>API: Forward to backend replica
    API->>R: Check rate limit and idempotency
    API->>DB: Begin transaction
    API->>DB: Lock section row FOR UPDATE
    API->>DB: Check eligibility and capacity
    API->>DB: Insert enrollment or waitlist entry
    API->>DB: Commit
    API->>R: Invalidate/update section cache
    API->>MQ: Publish registration event
    API->>WS: Broadcast availability update
    API-->>S: Result
```

## 6. Project structure

```text
crsp-platform/
├─ docker-compose.yml
├─ .env.example
├─ README.md
├─ CHANGELOG.md
├─ docs/
├─ backend/
├─ frontend/
├─ worker/
├─ nginx/
├─ postgres/
└─ observability/
```

## 7. Architecture decisions

### ADR-001: Modular monolith

Use a modular monolith instead of microservices to avoid unnecessary distributed transactions while still supporting multiple replicas and workers.

### ADR-002: PostgreSQL as registration source of truth

Registration state is transactional. PostgreSQL provides constraints, row locks, and reliable writes.

### ADR-003: Redis is non-authoritative

Redis improves speed but cannot decide final enrollment.

### ADR-004: INS is optional for student flow

INS verification increases realism, but manual profile fallback protects the demo from external dependency risk.

### ADR-005: GPA skipped for manual profiles

Manual GPA is not trusted and should not affect eligibility.
