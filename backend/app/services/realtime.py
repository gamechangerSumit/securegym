from anyio.from_thread import run as run_from_thread
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
    try:
        run_from_thread(broadcast_event, payload)
    except RuntimeError:
        return
