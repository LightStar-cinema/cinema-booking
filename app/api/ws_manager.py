from collections import defaultdict

from fastapi import WebSocket
from starlette.websockets import WebSocketState


class ConnectionManager:
    """
    Tracks WebSocket connections grouped by showtime room.
    All methods are async-safe: asyncio is single-threaded so plain dicts are fine.
    """

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, room: str, ws: WebSocket) -> None:
        await ws.accept()
        self._rooms[room].add(ws)

    def disconnect(self, room: str, ws: WebSocket) -> None:
        self._rooms[room].discard(ws)
        if not self._rooms[room]:
            self._rooms.pop(room, None)

    def subscriber_count(self, room: str) -> int:
        return len(self._rooms.get(room, set()))

    async def broadcast(self, room: str, payload: dict) -> None:
        """Send payload to every live connection in room; silently prune dead ones."""
        dead: set[WebSocket] = set()
        for ws in list(self._rooms.get(room, set())):
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(payload)
                else:
                    dead.add(ws)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._rooms[room].discard(ws)


# Module-level singleton shared across all routers
manager = ConnectionManager()
