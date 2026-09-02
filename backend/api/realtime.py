"""In-process real-time event stream for the Week 4 control room."""

import asyncio
import json
from collections import deque
from datetime import datetime, timezone
from threading import Lock

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from backend.api.prediction import PredictionRequest, predict_scenario


router = APIRouter(prefix="/api/realtime", tags=["real-time"])


class EventBroker:
    def __init__(self, history_size=100):
        self._events = deque(maxlen=history_size)
        self._lock = Lock()
        self._next_id = 1

    def publish(self, event_type, payload):
        with self._lock:
            event = {
                "id": self._next_id,
                "type": event_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
            }
            self._next_id += 1
            self._events.append(event)
        return event

    def events_since(self, event_id):
        with self._lock:
            return [
                event.copy()
                for event in self._events
                if event["id"] > event_id
            ]


broker = EventBroker()


def publish_event(event_type, payload):
    return broker.publish(event_type, payload)


def _sse_message(event):
    data = json.dumps(event, separators=(",", ":"))
    return f"id: {event['id']}\nevent: {event['type']}\ndata: {data}\n\n"


@router.get("/events")
async def event_stream(request: Request):
    last_event_id = request.headers.get("Last-Event-ID", "0")
    try:
        cursor = int(last_event_id)
    except ValueError:
        cursor = 0

    async def generate():
        nonlocal cursor
        yield ": connected\n\n"
        heartbeat = 0

        while not await request.is_disconnected():
            events = broker.events_since(cursor)
            for event in events:
                cursor = event["id"]
                yield _sse_message(event)

            heartbeat += 1
            if heartbeat >= 15:
                yield ": heartbeat\n\n"
                heartbeat = 0

            await asyncio.sleep(1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/scenarios")
def publish_scenario(request: PredictionRequest):
    prediction = predict_scenario(request)
    event = publish_event(
        "prediction.updated",
        {"prediction": prediction, "source": "controlled_demo"},
    )
    return {"event": event, "prediction": prediction}
