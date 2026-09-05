from __future__ import annotations
from enum import Enum
import asyncio


class ProcessingStatus(Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"


class IdempotencyStore:
    def __init__(self):
        self._states: dict[str, ProcessingStatus] = {}
        self._lock = asyncio.Lock()

    async def claim(self, incident_id: str) -> bool:
        async with self._lock:
            if incident_id in self._states:
                return False
            self._states[incident_id] = ProcessingStatus.PROCESSING
            return True

    async def complete(self, incident_id: str):
        async with self._lock:
            self._states[incident_id] = ProcessingStatus.COMPLETED

    async def release(self, incident_id: str):
        async with self._lock:
            if incident_id in self._states:
                del self._states[incident_id]

    async def status(self, incident_id: str) -> ProcessingStatus | None:
        async with self._lock:
            return self._states.get(incident_id)


idempotency_store = IdempotencyStore()
