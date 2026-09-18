"""Knowledge pack endpoints — GET and POST /finalize."""

from fastapi import APIRouter, HTTPException

from orchestrator.models.knowledge_pack import KnowledgePack
from orchestrator.services.pack_builder import finalize_pack, build_knowledge_pack
from orchestrator.services.session import session_store

router = APIRouter(tags=["knowledge-pack"])


@router.get("/knowledge-pack/{session_id}", response_model=KnowledgePack)
async def get_knowledge_pack(session_id: str) -> KnowledgePack:
    """Retrieve the knowledge pack for a session (may be partial if not finalized)."""
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return build_knowledge_pack(session)


@router.post("/finalize", response_model=KnowledgePack)
async def handle_finalize(session_id: str) -> KnowledgePack:
    """Finalize the exploration and produce the compact knowledge pack.

    Query parameter: session_id
    """
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    pack = finalize_pack(session)
    return pack
