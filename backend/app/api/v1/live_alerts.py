from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.connection_manager import manager
import json

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def active_session_tunnel(websocket: WebSocket, user_id: str):
    """
    [P0] Persistent connection for the frontend to receive instant 
    escalation and deviation alerts from the server.
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # We keep the tunnel open. The client doesn't need to send 
            # anything here, but we listen just in case they send a heartbeat.
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)