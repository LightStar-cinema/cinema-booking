import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.ws_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/showtimes/{showtime_id}")
async def showtime_ws(ws: WebSocket, showtime_id: uuid.UUID) -> None:
    """
    Real-time seat availability stream for a single showtime.

    Connection lifecycle:
      1. Client connects → receives a "connected" envelope with viewer count.
      2. Server pushes "seat_status" events whenever seats are locked, booked,
         or released (cancelled / lock expired).
      3. Client can send "ping" to check liveness; server replies "pong".
      4. On disconnect the room is cleaned up automatically.

    Recommended client flow:
      • Call GET /api/showtimes/{id} once for the initial seat snapshot.
      • Then open this socket and apply incremental "seat_status" events on top.

    Event shapes
    ────────────
    → connected
    {
      "event": "connected",
      "showtime_id": "<uuid>",
      "viewers": 3
    }

    → seat_status  (status: "locked" | "booked" | "available")
    {
      "event": "seat_status",
      "showtime_id": "<uuid>",
      "seats": [
        {"seat_id": "<uuid>", "status": "booked"},
        ...
      ]
    }

    → pong
    { "event": "pong" }
    """
    room = str(showtime_id)
    await manager.connect(room, ws)
    try:
        await ws.send_json(
            {
                "event": "connected",
                "showtime_id": room,
                "viewers": manager.subscriber_count(room),
            }
        )

        while True:
            text = await ws.receive_text()
            if text == "ping":
                await ws.send_json({"event": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(room, ws)
