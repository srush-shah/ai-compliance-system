import asyncio
from typing import Dict, Set

import anyio
from fastapi import WebSocket


class RunUpdateManager:
    def __init__(self) -> None:
        self._connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, run_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(run_id, set()).add(websocket)

    async def disconnect(self, run_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._connections.get(run_id)
            if not connections:
                return
            connections.discard(websocket)
            if not connections:
                self._connections.pop(run_id, None)

    async def broadcast(self, run_id: int, message: dict) -> None:
        async with self._lock:
            connections = list(self._connections.get(run_id, set()))

        if not connections:
            return

        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                stale.append(websocket)

        if stale:
            async with self._lock:
                for websocket in stale:
                    connections = self._connections.get(run_id)
                    if not connections:
                        break
                    connections.discard(websocket)
                    if not connections:
                        self._connections.pop(run_id, None)

    def broadcast_sync(self, run_id: int, message: dict) -> None:
        try:
            anyio.from_thread.run(self.broadcast, run_id, message)
        except RuntimeError:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return
            loop.create_task(self.broadcast(run_id, message))


run_update_manager = RunUpdateManager()
