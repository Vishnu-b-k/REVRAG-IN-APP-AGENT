"""Screen ingestion service — core pipeline for /ingest-screen.

Takes a validated ObservationRequest, runs it through the LLM provider,
normalises the raw result into an IngestScreenResponse, records events,
and returns the typed response.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from orchestrator.models.action import (
    ActionType,
    CandidateAction,
    IngestScreenResponse,
    NextAction,
    ScreenElement,
)
from orchestrator.models.observation import ObservationRequest
from orchestrator.providers.base import LLMProvider, LLMProviderError, ScreenAnalysis
from orchestrator.services.session import EventType, SessionState

logger = logging.getLogger(__name__)


async def ingest_screen(
    request: ObservationRequest,
    session: SessionState,
    provider: LLMProvider,
) -> IngestScreenResponse:
    """Full ingestion pipeline for one screen observation.

    1. Record the observation event.
    2. Call the LLM provider.
    3. Normalise raw output → typed models.
    4. Generate screen / state IDs.
    5. Record the model response event.
    6. Return the typed response.
    """

    # 1. Record observation
    session.current_step = request.step
    session.record_event(
        EventType.OBSERVATION,
        step=request.step,
        data={
            "session_id": request.session_id,
            "previous_state_id": request.previous_state_id,
            "ui_tree_package": request.ui_tree.package_name,
            "ui_tree_activity": request.ui_tree.activity_name,
        },
    )

    # 2. Call the provider
    ui_tree_dict = request.ui_tree.model_dump()
    context = session.get_exploration_context()

    try:
        analysis: ScreenAnalysis = await provider.analyse_screen(
            screenshot_b64=request.screenshot_b64,
            ui_tree=ui_tree_dict,
            exploration_context=context,
        )
    except LLMProviderError as exc:
        logger.error("Provider %s failed: %s", provider.name, exc)
        # Safe fallback — return null action so Android stops gracefully
        state_id = _make_state_id(request)
        session.record_event(
            EventType.MODEL_RESPONSE,
            step=request.step,
            data={"error": str(exc), "provider": provider.name},
        )
        return IngestScreenResponse(
            screen_id=f"scr_error_{request.step}",
            state_id=state_id,
            is_new_screen=False,
            description=f"Provider error: {exc}",
            next_action=NextAction(
                type=ActionType.NULL,
                reason=f"Provider error: {exc}",
                confidence=0.0,
            ),
        )

    # 3. Normalise into typed models
    elements = _normalise_elements(analysis.elements)
    candidate_actions = _normalise_candidates(analysis.candidate_actions)
    next_action = _normalise_next_action(analysis.next_action)

    # 4. Generate IDs
    state_id = _make_state_id(request)
    screen_id = _make_screen_id(request)
    is_new = screen_id not in session.screens_seen

    if is_new:
        session.screens_seen[screen_id] = {
            "purpose": analysis.screen_purpose,
            "first_step": request.step,
        }

    # Track attempted actions
    if next_action.type != ActionType.NULL and next_action.target_element_id:
        action_key = f"{next_action.type.value}:{next_action.target_element_id}"
        session.attempted_actions.append(action_key)

    # 5. Record model response
    session.current_state_id = state_id
    session.record_event(
        EventType.MODEL_RESPONSE,
        step=request.step,
        data={
            "provider": provider.name,
            "screen_id": screen_id,
            "state_id": state_id,
            "is_new_screen": is_new,
            "purpose": analysis.screen_purpose,
            "element_count": len(elements),
            "elements": [el.model_dump() for el in elements],
            "ui_tree": ui_tree_dict,
            "next_action_type": next_action.type.value,
            "confidence": next_action.confidence,
        },
    )

    # 6. Return typed response
    return IngestScreenResponse(
        screen_id=screen_id,
        state_id=state_id,
        is_new_screen=is_new,
        description=analysis.screen_purpose,
        elements=elements,
        candidate_actions=candidate_actions,
        next_action=next_action,
    )


# ── Normalisation helpers ────────────────────────────────────────────


def _normalise_elements(raw: list[dict[str, Any]]) -> list[ScreenElement]:
    """Convert raw element dicts to ScreenElement models, skipping invalid."""
    result: list[ScreenElement] = []
    for el in raw:
        try:
            result.append(ScreenElement(
                id=str(el.get("id", "")),
                role=str(el.get("role", "unknown")),
                label=str(el.get("label", "")),
                bounds=el.get("bounds", [0, 0, 0, 0]),
                actions=el.get("actions", []),
            ))
        except Exception:
            logger.warning("Skipping malformed element: %s", el)
    return result


def _normalise_candidates(raw: list[dict[str, Any]]) -> list[CandidateAction]:
    """Convert raw candidate dicts, dropping any with invalid action types."""
    result: list[CandidateAction] = []
    for ca in raw:
        try:
            action_type = ActionType(ca["type"])
            confidence = max(0.0, min(1.0, float(ca.get("confidence", 0.0))))
            result.append(CandidateAction(
                type=action_type,
                target_element_id=ca.get("target_element_id"),
                value=ca.get("value"),
                reason=ca.get("reason", ""),
                confidence=confidence,
            ))
        except (ValueError, KeyError) as exc:
            logger.warning("Dropping invalid candidate action: %s (%s)", ca, exc)
    return result


def _normalise_next_action(raw: dict[str, Any]) -> NextAction:
    """Convert raw next-action dict to NextAction, falling back to null."""
    try:
        action_type = ActionType(raw["type"])
        confidence = max(0.0, min(1.0, float(raw.get("confidence", 0.0))))
        return NextAction(
            type=action_type,
            target_element_id=raw.get("target_element_id"),
            value=raw.get("value"),
            reason=raw.get("reason", ""),
            confidence=confidence,
        )
    except (ValueError, KeyError) as exc:
        logger.warning("Malformed next_action, falling back to null: %s (%s)", raw, exc)
        return NextAction(
            type=ActionType.NULL,
            reason=f"Malformed model output: {exc}",
            confidence=0.0,
        )


def _make_state_id(request: ObservationRequest) -> str:
    """Generate a state ID from the observation content."""
    hasher = hashlib.sha256()
    hasher.update(request.session_id.encode())
    hasher.update(str(request.step).encode())
    # Include a compact tree fingerprint
    tree_str = json.dumps(
        request.ui_tree.model_dump(),
        sort_keys=True,
        separators=(",", ":"),
    )
    hasher.update(tree_str.encode())
    return f"state_{hasher.hexdigest()[:12]}"


def _make_screen_id(request: ObservationRequest) -> str:
    """Generate a screen ID from structural tree features.

    NOTE: This is a *naive* ID for V-1.  V-3 replaces it with canonical
    fingerprinting + deduplication.
    """
    activity = request.ui_tree.activity_name or "unknown"
    # Use activity as the primary screen discriminator for now
    hasher = hashlib.sha256()
    hasher.update(activity.encode())
    return f"scr_{hasher.hexdigest()[:8]}"
