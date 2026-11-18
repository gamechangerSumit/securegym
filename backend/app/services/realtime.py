import asyncio

from fastapi import WebSocket

_connections: set[WebSocket] = set()


async def connect(websocket: WebSocket) -> None:
    await websocket.accept()
    _connections.add(websocket)


def disconnect(websocket: WebSocket) -> None:
    _connections.discard(websocket)


async def broadcast_event(payload: dict) -> None:
    stale: list[WebSocket] = []
    for socket in list(_connections):
        try:
            await socket.send_json(payload)
        except Exception:
            stale.append(socket)
    for socket in stale:
        disconnect(socket)


def publish_event(payload: dict) -> None:
    """Schedule event delivery when called from an async request context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(broadcast_event(payload))
