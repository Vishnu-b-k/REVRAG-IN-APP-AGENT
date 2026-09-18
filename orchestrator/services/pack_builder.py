"""Knowledge pack generation and compaction.

Builds the final KnowledgePack from session event logs, applying
canonicalisation, deduplication, and stable ordering.

Phase V-4 of the execution plan.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from orchestrator.models.knowledge_pack import (
    DesignTokens,
    GlobalDesignSystem,
    Journey,
    KnowledgePack,
    ScanMetadata,
    Screen,
    Transition,
)
from orchestrator.services.fingerprint import (
    ScreenDeduplicator,
    compute_fingerprint,
    compute_screen_id,
)
from orchestrator.services.session import EventType, SessionState

logger = logging.getLogger(__name__)


def build_knowledge_pack(session: SessionState) -> KnowledgePack:
    """Build a complete knowledge pack from a session's event log.

    Steps:
    1. Extract screen observations from events.
    2. Canonicalise and deduplicate screens.
    3. Build transitions from state graph (prefer controller data).
    4. Infer journeys from event sequence.
    5. Attach design_tokens placeholders.
    6. Compute scan metadata.
    7. Apply stable ordering.
    """

    start_time = time.time()

    # Use session's deduplicator if available, else create a new one
    dedup = getattr(session, 'deduplicator', None) or ScreenDeduplicator()
    controller = getattr(session, 'exploration_controller', None)

    screens: dict[str, Screen] = {}
    transitions: list[Transition] = []
    seen_transitions: set[str] = set()
    journey_steps: list[str] = []

    # ── 1. Process events to extract screen data ─────────────────────

    for event in session.events:
        if event.event_type == EventType.MODEL_RESPONSE:
            data = event.data

            screen_id = data.get("screen_id", "")
            if not screen_id:
                continue

            # Build screen if not already captured
            if screen_id not in screens:
                screens[screen_id] = Screen(
                    id=screen_id,
                    fingerprint=data.get("fingerprint", ""),
                    name=_infer_screen_name(screen_id, data),
                    purpose=data.get("purpose", ""),
                    screenshot_url=data.get("screenshot_url"),
                    elements=data.get("elements", []),
                    forms=_extract_forms(data.get("elements", [])),
                    design_tokens=DesignTokens(),  # Placeholder for Slaven (S-1)
                )

            # Track journey
            if screen_id not in journey_steps or journey_steps[-1] != screen_id:
                journey_steps.append(screen_id)

        elif event.event_type == EventType.OBSERVATION:
            data = event.data
            prev = data.get("previous_state_id")
            # Transitions are built from consecutive screen visits below

    # ── 2. Build transitions ────────────────────────────────────────
    # Prefer exploration controller transitions (richer action data)

    if controller and controller.transitions:
        for t in controller.transitions:
            from_state = t.get("from", "")
            to_state = t.get("to", "")
            # Map state_ids back to screen_ids via the controller's state graph
            from_node = controller.states.get(from_state)
            to_node = controller.states.get(to_state)
            if from_node and to_node:
                from_scr = from_node.screen_id
                to_scr = to_node.screen_id
                transition_key = f"{from_scr}->{to_scr}"
                if transition_key not in seen_transitions and from_scr != to_scr:
                    seen_transitions.add(transition_key)
                    transitions.append(Transition(
                        **{
                            "from": from_scr,
                            "to": to_scr,
                            "action": t.get("action", {"step": t.get("step", 0)}),
                        }
                    ))
    else:
        # Fallback: infer transitions from journey sequence
        for i in range(len(journey_steps) - 1):
            from_id = journey_steps[i]
            to_id = journey_steps[i + 1]
            transition_key = f"{from_id}->{to_id}"

            if transition_key not in seen_transitions and from_id != to_id:
                seen_transitions.add(transition_key)
                transitions.append(Transition(
                    **{
                        "from": from_id,
                        "to": to_id,
                        "action": {"step": i},
                    }
                ))

    # ── 3. Build journeys ────────────────────────────────────────────

    journeys = []
    if journey_steps:
        # Main exploration journey
        # Deduplicate consecutive duplicates for a clean journey
        clean_steps = [journey_steps[0]]
        for step in journey_steps[1:]:
            if step != clean_steps[-1]:
                clean_steps.append(step)

        journeys.append(Journey(
            name="Main Exploration",
            steps=clean_steps,
        ))

    # ── 4. Stable ordering ───────────────────────────────────────────

    sorted_screens = sorted(screens.values(), key=lambda s: s.id)
    sorted_transitions = sorted(
        transitions,
        key=lambda t: (t.from_screen, t.to_screen),
    )

    # ── 5. Scan metadata ─────────────────────────────────────────────

    duration = time.time() - session.created_at

    pack = KnowledgePack(
        schema_version="1.0",
        app_metadata=_build_app_metadata(session),
        screens=sorted_screens,
        transitions=sorted_transitions,
        journeys=journeys,
        global_design_system=GlobalDesignSystem(),  # Placeholder for Slaven (S-2)
        scan_metadata=ScanMetadata(
            total_steps=session.current_step + 1,
            screens_discovered=len(screens),
            transitions_discovered=len(transitions),
            duplicates_merged=dedup.duplicates_merged,
            exploration_duration_seconds=round(duration, 2),
            pack_size_bytes=0,  # Filled below
        ),
    )

    # ── 6. Calculate pack size ───────────────────────────────────────

    pack_json = pack.model_dump_json(indent=None)
    pack.scan_metadata.pack_size_bytes = len(pack_json.encode("utf-8"))

    return pack


def finalize_pack(session: SessionState) -> KnowledgePack:
    """Finalize a session into a compact knowledge pack.

    This is the main entry point for POST /finalize.
    Records a session_end event and builds the pack.
    """
    session.record_event(
        EventType.SESSION_END,
        step=session.current_step,
        data={"reason": "finalize"},
    )

    pack = build_knowledge_pack(session)

    logger.info(
        "Finalized pack for session %s: %d screens, %d transitions, %d bytes",
        session.session_id,
        pack.scan_metadata.screens_discovered,
        pack.scan_metadata.transitions_discovered,
        pack.scan_metadata.pack_size_bytes,
    )

    return pack


# ── Helpers ──────────────────────────────────────────────────────────


def _infer_screen_name(screen_id: str, data: dict[str, Any]) -> str:
    """Derive a human-readable name from available data."""
    purpose = data.get("purpose", "")
    if purpose:
        # Take first phrase / sentence
        name = purpose.split(".")[0].split("/")[0].strip()
        # Capitalize and truncate
        return name[:50] if name else screen_id
    return screen_id


def _extract_forms(elements: list[dict[str, Any]]) -> list:
    """Extract form fields from elements that are editable / text_input."""
    forms = []
    for el in elements:
        role = el.get("role", "")
        if role in ("text_input", "checkbox", "toggle", "dropdown"):
            forms.append({
                "id": el.get("id", ""),
                "label": el.get("label", ""),
                "input_type": _role_to_input_type(role),
                "required": False,
            })
    return forms


def _role_to_input_type(role: str) -> str:
    """Map semantic role to input type."""
    mapping = {
        "text_input": "text",
        "checkbox": "checkbox",
        "toggle": "toggle",
        "dropdown": "dropdown",
    }
    return mapping.get(role, "text")


def _build_app_metadata(session: SessionState) -> dict[str, Any]:
    """Build app metadata from session data."""
    metadata: dict[str, Any] = {
        "session_id": session.session_id,
    }

    # Try to extract package name from first observation
    for event in session.events:
        if event.event_type == EventType.OBSERVATION:
            pkg = event.data.get("ui_tree_package")
            if pkg:
                metadata["package_name"] = pkg
                break

    return metadata
