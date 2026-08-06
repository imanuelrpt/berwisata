"""WebSocket connection manager for real-time location tracking."""
import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import WebSocket

from app.core.config import settings

logger = logging.getLogger("app.ws")

ClientID = str


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[ClientID, WebSocket] = {}
        self._user_map: dict[int, set[ClientID]] = {}
        self._locations: dict[int, dict[str, float]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, client_id: ClientID, user_id: Optional[int]) -> None:
        await ws.accept()
        async with self._lock:
            if len(self._connections) >= settings.WS_MAX_CLIENTS:
                await ws.close(code=1013)
                return
            self._connections[client_id] = ws
            if user_id is not None:
                self._user_map.setdefault(user_id, set()).add(client_id)

    async def disconnect(self, client_id: ClientID, user_id: Optional[int]) -> None:
        async with self._lock:
            self._connections.pop(client_id, None)
            if user_id is not None and user_id in self._user_map:
                self._user_map[user_id].discard(client_id)
                if not self._user_map[user_id]:
                    self._user_map.pop(user_id, None)
                    self._locations.pop(user_id, None)

    async def handle_location(self, client_id: ClientID, user_id: Optional[int], data: dict[str, Any]) -> Optional[dict]:
        """Store location and return a computed nearby payload if movement is significant."""
        try:
            lat = float(data.get("latitude"))
            lon = float(data.get("longitude"))
            accuracy = float(data.get("accuracy", 0))
        except (TypeError, ValueError):
            return None

        result: dict[str, Any] = {"type": "ack", "latitude": lat, "longitude": lon}
        if user_id is not None:
            async with self._lock:
                prev = self._locations.get(user_id)
                self._locations[user_id] = {"latitude": lat, "longitude": lon, "accuracy": accuracy}
            if prev and self._moved(prev["latitude"], prev["longitude"], lat, lon, 0.3):
                result["type"] = "moved"
            await self.broadcast_to_user(user_id, {
                "type": "peer_location",
                "user_id": user_id,
                "latitude": lat,
                "longitude": lon,
                "accuracy": accuracy,
            })
        else:
            result["nearby_computed"] = True
        return result

    @staticmethod
    def _moved(lat1: float, lon1: float, lat2: float, lon2: float, threshold_km: float) -> bool:
        from app.utils.geo import haversine_km

        return haversine_km(lat1, lon1, lat2, lon2) > threshold_km

    async def send_to_client(self, client_id: ClientID, message: dict[str, Any]) -> None:
        ws = self._connections.get(client_id)
        if ws:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                self._connections.pop(client_id, None)

    async def broadcast_to_user(self, user_id: int, message: dict[str, Any]) -> None:
        client_ids = list(self._user_map.get(user_id, set()))
        text = json.dumps(message)
        for cid in client_ids:
            ws = self._connections.get(cid)
            if ws:
                try:
                    await ws.send_text(text)
                except Exception:
                    self._connections.pop(cid, None)

    def latest_location(self, user_id: int) -> Optional[dict[str, float]]:
        return self._locations.get(user_id)


manager = ConnectionManager()
