from collections import defaultdict

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self.section_connections: dict[int, set[WebSocket]] = defaultdict(set)
        self.user_connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect_section(self, section_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.section_connections[section_id].add(websocket)

    async def connect_user(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.user_connections[user_id].add(websocket)

    def disconnect_section(self, section_id: int, websocket: WebSocket) -> None:
        self.section_connections[section_id].discard(websocket)

    def disconnect_user(self, user_id: int, websocket: WebSocket) -> None:
        self.user_connections[user_id].discard(websocket)

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


manager = WebSocketManager()
