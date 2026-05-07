# 08 — Observability

## 1. Goal

CRSP must collect traces, logs, and metrics in one observability backend. The main action to demonstrate should be:

> Student registration attempt from request to database transaction to event publishing to live update.

## 2. Stack options

Recommended default:

```text
OpenTelemetry Collector
+ Prometheus
+ Grafana
+ Loki
+ Tempo
```

Simpler alternative:

```text
SigNoz all-in-one
```

Use SigNoz if the Grafana stack becomes too time-consuming.

## 3. Traces

Instrument:

- FastAPI requests;
- PostgreSQL queries;
- Redis calls;
- RabbitMQ publish/consume;
- Celery worker tasks;
- INS sync calls if implemented;
- timetable suggestion worker.

Important trace:

```text
POST /api/v1/registrations
  -> rate_limit_check
  -> idempotency_check
  -> load_student_profile
  -> lock_section_for_update
  -> eligibility_checks
  -> insert_enrollment_or_waitlist
  -> commit_transaction
  -> publish_rabbitmq_event
  -> websocket_broadcast
```

## 4. Logs

Use structured JSON logs.

Example:

```json
{
  "level": "INFO",
  "event": "registration_succeeded",
  "trace_id": "abc123",
  "student_number": "2310204",
  "profile_source": "manual",
  "gpa_rule": "skipped_manual_profile",
  "section_id": 101,
  "remaining_seats": 4
}
```

Log events:

- `ins_login_succeeded`;
- `ins_sync_failed`;
- `manual_profile_created`;
- `professor_room_selected`;
- `timetable_suggestion_completed`;
- `registration_succeeded`;
- `registration_failed`;
- `student_waitlisted`;
- `rate_limit_rejected`.

## 5. Metrics

Recommended Prometheus metrics:

```text
http_requests_total
http_request_duration_seconds
registration_attempts_total
registration_success_total
registration_failures_total
registration_waitlisted_total
manual_profile_created_total
ins_sync_success_total
ins_sync_failure_total
professor_room_selection_total
timetable_suggestion_runs_total
rate_limit_rejections_total
redis_cache_hits_total
redis_cache_misses_total
rabbitmq_messages_published_total
celery_task_duration_seconds
```

Labels:

```text
route
method
status_code
profile_source
rule_failure_reason
section_id
```

Avoid high-cardinality labels for production; for demo, section_id can be acceptable.

## 6. Correlation IDs

Every request should have:

- `X-Request-ID`;
- trace ID;
- user ID/student number if authenticated;
- service name.

Nginx should forward request ID to backend.

## 7. Required report screenshots

Capture at least:

1. One distributed trace for successful registration.
2. One log query filtered by trace ID.
3. One metric graph showing registration attempts or API latency.
4. Optional: RabbitMQ queue metrics.
5. Optional: Redis cache hit/miss graph.

## 8. Observability acceptance checklist

- [ ] FastAPI emits traces.
- [ ] Worker emits traces.
- [ ] Logs include trace IDs.
- [ ] Metrics endpoint is scraped by Prometheus.
- [ ] Dashboard shows registration activity.
- [ ] At least one failed registration is visible in logs.
- [ ] Manual-profile GPA skip is visible in logs/audit.
- [ ] INS sync success/failure is visible if implemented.
