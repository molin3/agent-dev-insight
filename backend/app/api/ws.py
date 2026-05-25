"""WebSocket 实时推送"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}
        self._trace_subscribers: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()

    def disconnect(self, websocket: WebSocket) -> None:
        for conns in self._connections.values():
            conns.discard(websocket)
        for conns in self._trace_subscribers.values():
            conns.discard(websocket)

    def subscribe_project(self, project_id: str, websocket: WebSocket) -> None:
        if project_id not in self._connections:
            self._connections[project_id] = set()
        self._connections[project_id].add(websocket)

    def subscribe_trace(self, trace_id: str, websocket: WebSocket) -> None:
        if trace_id not in self._trace_subscribers:
            self._trace_subscribers[trace_id] = set()
        self._trace_subscribers[trace_id].add(websocket)

    async def send_to_project(self, project_id: str, message: dict) -> None:
        dead = set()
        for ws in self._connections.get(project_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_to_trace(self, trace_id: str, message: dict) -> None:
        dead = set()
        for ws in self._trace_subscribers.get(trace_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcast(self, message: dict) -> None:
        all_ws = set()
        for conns in self._connections.values():
            all_ws.update(conns)
        for conns in self._trace_subscribers.values():
            all_ws.update(conns)

        dead = set()
        for ws in all_ws:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")

            if msg_type == "subscribe":
                if "project_id" in msg:
                    manager.subscribe_project(msg["project_id"], websocket)
                if "trace_id" in msg:
                    manager.subscribe_trace(msg["trace_id"], websocket)

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.error("WebSocket error", exc_info=True)
    finally:
        manager.disconnect(websocket)
