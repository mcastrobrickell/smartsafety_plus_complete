"""
SmartSafety+ - WebSocket Manager
Manages real-time connections for live notifications and dashboard updates.

Usage:
    from utils.websocket import ws_manager

    # In any router, broadcast an event:
    await ws_manager.broadcast({
        "type": "new_finding",
        "severity": "critico",
        "message": "Nuevo hallazgo crítico detectado"
    })

    # Or send to a specific user:
    await ws_manager.send_to_user(user_id, {...})
"""
from fastapi import WebSocket
from typing import Dict, List, Any
from config import logger
import json


class WebSocketManager:
    """Manages active WebSocket connections by user_id."""

    def __init__(self):
        # {user_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # All connections (for broadcast)
        self.all_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: str = "anonymous"):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.all_connections.append(websocket)
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"🔌 WebSocket connected: {user_id} (total: {len(self.all_connections)})")

    def disconnect(self, websocket: WebSocket, user_id: str = "anonymous"):
        """Remove a WebSocket connection."""
        if websocket in self.all_connections:
            self.all_connections.remove(websocket)
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"🔌 WebSocket disconnected: {user_id} (total: {len(self.all_connections)})")

    async def broadcast(self, data: dict):
        """Send a message to ALL connected clients."""
        message = json.dumps(data, ensure_ascii=False, default=str)
        disconnected = []
        for ws in self.all_connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        # Clean up dead connections
        for ws in disconnected:
            self.all_connections.remove(ws)

    async def send_to_user(self, user_id: str, data: dict):
        """Send a message to a specific user's connections."""
        if user_id not in self.active_connections:
            return
        message = json.dumps(data, ensure_ascii=False, default=str)
        disconnected = []
        for ws in self.active_connections[user_id]:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.active_connections[user_id].remove(ws)
            if ws in self.all_connections:
                self.all_connections.remove(ws)

    async def send_to_role(self, role: str, data: dict, db=None):
        """Send to all users with a specific role (needs db to lookup)."""
        if not db:
            return
        users = await db.users.find({"role": role}, {"id": 1}).to_list(100)
        for user in users:
            await self.send_to_user(user.get("id", ""), data)

    @property
    def connection_count(self) -> int:
        return len(self.all_connections)

    @property
    def connected_users(self) -> List[str]:
        return list(self.active_connections.keys())


# Global singleton
ws_manager = WebSocketManager()
