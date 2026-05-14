import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket
from redis.exceptions import RedisError

from app.core.logging import get_logger
from app.core.metrics import set_websocket_connections
from app.modules.platform.redis_client import create_async_redis_client

logger = get_logger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self.section_connections: dict[int, set[WebSocket]] = defaultdict(set)
        self.user_connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect_section(self, section_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.section_connections[section_id].add(websocket)
        self._refresh_metrics()

    async def connect_user(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.user_connections[user_id].add(websocket)
        self._refresh_metrics()

    def disconnect_section(self, section_id: int, websocket: WebSocket) -> None:
        self.section_connections[section_id].discard(websocket)
        if not self.section_connections[section_id]:
            self.section_connections.pop(section_id, None)
        self._refresh_metrics()

    def disconnect_user(self, user_id: int, websocket: WebSocket) -> None:
        self.user_connections[user_id].discard(websocket)
        if not self.user_connections[user_id]:
            self.user_connections.pop(user_id, None)
        self._refresh_metrics()

    async def broadcast_section(self, section_id: int, payload: dict) -> None:
        stale: list[WebSocket] = []
        for websocket in self.section_connections[section_id]:
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect_section(section_id, websocket)

    async def broadcast_user(self, user_id: int, payload: dict) -> None:
        stale: list[WebSocket] = []
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect_user(user_id, websocket)

    async def listen_for_redis_section_events(self, stop_event: asyncio.Event) -> None:
        """Bridge Redis pub/sub events into local WebSocket connections."""

        client = create_async_redis_client()
        if client is None:
            return

        pubsub = client.pubsub()
        try:
            await pubsub.psubscribe("section:*:availability")
            while not stop_event.is_set():
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message is None:
                    continue
                channel = str(message["channel"])
                section_id = self._section_id_from_channel(channel)
                if section_id is None:
                    continue
                payload = json.loads(message["data"])
                await self.broadcast_section(section_id, payload)
        except (RedisError, json.JSONDecodeError) as exc:
            logger.warning("websocket.redis_bridge_stopped", error=str(exc))
        finally:
            await pubsub.close()
            await client.aclose()

    def _refresh_metrics(self) -> None:
        section_count = sum(len(items) for items in self.section_connections.values())
        user_count = sum(len(items) for items in self.user_connections.values())
        set_websocket_connections("section", section_count)
        set_websocket_connections("user", user_count)

    @staticmethod
    def _section_id_from_channel(channel: str) -> int | None:
        parts = channel.split(":")
        if len(parts) != 3 or parts[0] != "section":
            return None
        try:
            return int(parts[1])
        except ValueError:
            return None


manager = WebSocketManager()
