from __future__ import annotations

from threading import Lock
from uuid import uuid4

from app.models.domain import AgentState


class AgentMemoryStore:
    def __init__(self) -> None:
        self._items: dict[str, AgentState] = {}
        self._lock = Lock()

    def create(self, state: AgentState) -> str:
        session_id = str(uuid4())
        with self._lock:
            self._items[session_id] = state
        return session_id

    def get(self, session_id: str) -> AgentState | None:
        with self._lock:
            return self._items.get(session_id)

    def update(self, session_id: str, state: AgentState) -> None:
        with self._lock:
            self._items[session_id] = state
