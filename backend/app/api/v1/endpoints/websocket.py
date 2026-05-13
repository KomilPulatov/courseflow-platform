from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.modules.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/sections/{section_id}")
async def section_socket(websocket: WebSocket, section_id: int) -> None:
    await manager.connect_section(section_id, websocket)
    await websocket.send_json({"type": "connected", "section_id": section_id})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_section(section_id, websocket)


@router.websocket("/ws/registrations/{user_id}")
async def registration_socket(websocket: WebSocket, user_id: int) -> None:
    await manager.connect_user(user_id, websocket)
    await websocket.send_json({"type": "connected", "user_id": user_id})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_user(user_id, websocket)
