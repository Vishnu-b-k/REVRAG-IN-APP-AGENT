from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orchestrator.services.session import session_store

router = APIRouter(prefix="/sessions", tags=["sessions"])

class SessionStats(BaseModel):
    session_id: str
    total_events: int
    current_step: int
    screens_seen: int
    attempted_actions: int

@router.get("")
def list_sessions():
    return session_store.list_sessions()

@router.get("/{session_id}/stats", response_model=SessionStats)
def get_session_stats(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return SessionStats(
        session_id=session.session_id,
        total_events=len(session.events),
        current_step=session.current_step,
        screens_seen=len(session.screens_seen),
        attempted_actions=len(session.attempted_actions)
    )
