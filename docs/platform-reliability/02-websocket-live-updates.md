# WebSocket Live Updates

## File Locations

- `backend/app/api/v1/endpoints/websocket.py`
- `backend/app/modules/websocket/manager.py`
- `backend/app/main.py`
- `backend/app/modules/registration/availability.py`
- `backend/app/modules/registration/publishers.py`

## What Was Already Present

The project already had WebSocket routes:

- `/ws/sections/{section_id}`
- `/ws/registrations/{user_id}`

It also had an in-memory connection manager. That works when only one backend process exists, but it does
not work reliably with multiple backend replicas because a client may be connected to `backend-1` while a
registration write happens on `backend-2`.

## What Was Added

`WebSocketManager.listen_for_redis_section_events(...)` was added in
`backend/app/modules/websocket/manager.py`.

It subscribes to this Redis pattern:

```python
await pubsub.psubscribe("section:*:availability")
```

When Redis receives a message such as `section:12:availability`, every backend replica receives it. The
manager extracts the section id and broadcasts the JSON payload to local WebSocket clients connected to
that section.

## Startup Hook

`backend/app/main.py` starts the Redis bridge during FastAPI startup:

```python
if settings.WEBSOCKET_REDIS_BRIDGE_ENABLED:
    bridge_task = asyncio.create_task(manager.listen_for_redis_section_events(bridge_stop_event))
```

The task is cancelled during shutdown so the app exits cleanly.

## Broadcast Flow

The complete live-update flow is:

1. A student registers, drops, joins a waitlist, or cancels a waitlist entry.
2. The service commits the database transaction.
3. `RedisAvailabilityPublisher` calculates fresh section availability.
4. It publishes the availability payload to Redis.
5. Each backend replica receives the Redis message.
6. Each replica forwards the payload to WebSocket clients connected to that section.

## Metrics

The manager updates this gauge:

```python
crsp_websocket_connections{channel="section"}
crsp_websocket_connections{channel="user"}
```

That lets Prometheus and Grafana show how many WebSocket clients are currently connected.
