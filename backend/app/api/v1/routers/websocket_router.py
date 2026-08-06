from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/location")
async def location_socket(
    ws: WebSocket,
    token: str | None = Query(default=None),
    client_id: str | None = Query(default=None),
):
    user_id = None
    if token:
        try:
            payload = decode_token(token, expected_type="access")
            user_id = payload.get("uid")
        except ValueError:
            user_id = None

    cid = client_id or f"anon-{id(ws)}"
    await manager.connect(ws, cid, user_id)
    try:
        while True:
            data = await ws.receive_text()
            if data in ("__ping__", "ping"):
                await manager.send_to_client(cid, {"type": "pong"})
                continue
            import json as _json

            try:
                msg = _json.loads(data)
            except _json.JSONDecodeError:
                await manager.send_to_client(cid, {"type": "error", "message": "invalid json"})
                continue

            msg_type = msg.get("type", "location")
            if msg_type == "location":
                result = await manager.handle_location(cid, user_id, msg)
                if result:
                    await manager.send_to_client(cid, result)
            elif msg_type == "ping":
                await manager.send_to_client(cid, {"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect(cid, user_id)
    except Exception:
        await manager.disconnect(cid, user_id)
