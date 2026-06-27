from fastapi import WebSocket
from typing import Dict

class ConnectionManager:
    def __init__(self):
        # Maps a user_id to their active WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_alert(self, message: dict, user_id: str):
        """Pushes a JSON payload directly to a specific user's device."""
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)

manager = ConnectionManager()