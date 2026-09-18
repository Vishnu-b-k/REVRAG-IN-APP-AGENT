"""Session management and event logging.

Each exploration session gets an in-memory event log that records every
observation, model response, and action result.  The log is the source
of truth for V-2 (exploration state machine) and V-4 (knowledge pack
generation).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EventType(str, Enum):
    """Types of events recorded during exploration."""

    OBSERVATION = "observation"
    MODEL_RESPONSE = "model_response"
    ACTION_EXECUTED = "action_executed"
    ACTION_FAILED = "action_failed"
    BACKTRACK = "backtrack"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


@dataclass
class Event:
    """A single timestamped event in the exploration log."""

    event_type: EventType
    step: int
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    """In-memory state for one exploration session."""

    session_id: str
    created_at: float = field(default_factory=time.time)
    current_step: int = 0
    current_state_id: Optional[str] = None
    events: list[Event] = field(default_factory=list)
    screens_seen: dict[str, dict[str, Any]] = field(default_factory=dict)
    attempted_actions: list[str] = field(default_factory=list)

    def record_event(
        self,
        event_type: EventType,
        step: int,
        data: dict[str, Any] | None = None,
    ) -> Event:
        """Append an event to the session log and return it."""
        event = Event(event_type=event_type, step=step, data=data or {})
        self.events.append(event)
        return event

    def get_exploration_context(self) -> dict[str, Any]:
        """Build context dict for the LLM provider."""
        return {
            "session_id": self.session_id,
            "current_step": self.current_step,
            "screens_visited": list(self.screens_seen.keys()),
            "attempted_actions": self.attempted_actions,
            "total_events": len(self.events),
        }


class SessionStore:
    """Simple in-memory session store.

    Good enough for hackathon — a single Python process serves one
    exploration at a time.  Replace with Redis / DB for production.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        """Return existing session or create a new one."""
        if session_id not in self._sessions:
            session = SessionState(session_id=session_id)
            session.record_event(EventType.SESSION_START, step=0)
            self._sessions[session_id] = session
        return self._sessions[session_id]

    def get(self, session_id: str) -> Optional[SessionState]:
        """Return session if it exists, else None."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[str]:
        """Return all known session IDs."""
        return list(self._sessions.keys())


# Module-level singleton — shared across the app
session_store = SessionStore()
