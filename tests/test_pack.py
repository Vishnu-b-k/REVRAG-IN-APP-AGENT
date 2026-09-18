"""Tests for knowledge pack generation, endpoints, and stability.

Covers V-4 acceptance:
- Final pack is valid against schema.
- Same fixture scan twice produces stable IDs and structural ordering.
- Pack contains enough information for the viewer and rebuild test.
"""

import copy
import json

import pytest

from orchestrator.models.knowledge_pack import KnowledgePack
from orchestrator.services.pack_builder import build_knowledge_pack, finalize_pack
from orchestrator.services.session import EventType, SessionState


# ── Helpers ──────────────────────────────────────────────────────────

def _build_session_with_screens() -> SessionState:
    """Create a session with realistic events for 3 screens."""
    session = SessionState(session_id="test-pack-session")
    session.record_event(EventType.SESSION_START, step=0)

    # Screen 1: Login
    session.record_event(EventType.OBSERVATION, step=0, data={
        "session_id": "test-pack-session",
        "previous_state_id": None,
        "ui_tree_package": "com.revrag.targetapp",
        "ui_tree_activity": "LoginActivity",
    })
    session.record_event(EventType.MODEL_RESPONSE, step=0, data={
        "provider": "mock",
        "screen_id": "scr_login",
        "state_id": "state_001",
        "is_new_screen": True,
        "purpose": "User authentication / login screen",
        "element_count": 4,
        "next_action_type": "type_text",
        "confidence": 0.9,
        "elements": [
            {"id": "el_01", "role": "text_input", "label": "Phone", "bounds": [100, 700, 980, 800], "actions": ["type_text"]},
            {"id": "el_02", "role": "button", "label": "Send OTP", "bounds": [300, 870, 780, 960], "actions": ["tap"]},
        ],
    })

    # Screen 2: Dashboard
    session.record_event(EventType.OBSERVATION, step=1, data={
        "session_id": "test-pack-session",
        "previous_state_id": "state_001",
        "ui_tree_package": "com.revrag.targetapp",
        "ui_tree_activity": "DashboardActivity",
    })
    session.record_event(EventType.MODEL_RESPONSE, step=1, data={
        "provider": "mock",
        "screen_id": "scr_dashboard",
        "state_id": "state_002",
        "is_new_screen": True,
        "purpose": "Main dashboard showing key app sections",
        "element_count": 3,
        "next_action_type": "tap",
        "confidence": 0.85,
        "elements": [
            {"id": "el_10", "role": "button", "label": "Feed", "bounds": [50, 300, 520, 390], "actions": ["tap"]},
            {"id": "el_11", "role": "button", "label": "Profile", "bounds": [560, 300, 1030, 390], "actions": ["tap"]},
        ],
    })

    # Screen 3: Profile
    session.record_event(EventType.OBSERVATION, step=2, data={
        "session_id": "test-pack-session",
        "previous_state_id": "state_002",
        "ui_tree_package": "com.revrag.targetapp",
        "ui_tree_activity": "ProfileActivity",
    })
    session.record_event(EventType.MODEL_RESPONSE, step=2, data={
        "provider": "mock",
        "screen_id": "scr_profile",
        "state_id": "state_003",
        "is_new_screen": True,
        "purpose": "User profile screen",
        "element_count": 2,
        "next_action_type": "null",
        "confidence": 1.0,
        "elements": [
            {"id": "el_20", "role": "image", "label": "Avatar", "bounds": [340, 100, 740, 500], "actions": []},
            {"id": "el_21", "role": "label", "label": "User Name", "bounds": [200, 550, 880, 620], "actions": []},
        ],
    })

    session.current_step = 2
    return session


# ── Test: Pack Schema Validity ───────────────────────────────────────

class TestPackSchemaValidity:
    """Final pack must be valid against the KnowledgePack schema."""

    def test_build_produces_valid_pack(self):
        """build_knowledge_pack returns a valid KnowledgePack."""
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        assert isinstance(pack, KnowledgePack)
        assert pack.schema_version == "1.0"

    def test_finalize_produces_valid_pack(self):
        """finalize_pack returns a valid KnowledgePack."""
        session = _build_session_with_screens()
        pack = finalize_pack(session)
        assert isinstance(pack, KnowledgePack)

    def test_pack_serializes_to_json(self):
        """Pack should serialize cleanly to JSON."""
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        json_str = pack.model_dump_json()
        assert json_str
        # Validate it parses back
        loaded = KnowledgePack.model_validate_json(json_str)
        assert loaded.schema_version == "1.0"

    def test_sample_fixture_validates(self):
        """The sample_knowledge_pack.json fixture should validate."""
        with open("docs/sample_knowledge_pack.json") as f:
            data = json.load(f)
        pack = KnowledgePack.model_validate(data)
        assert len(pack.screens) == 4
        assert len(pack.transitions) == 3


# ── Test: Pack Content ───────────────────────────────────────────────

class TestPackContent:
    """Pack must contain screens, transitions, journeys, metadata."""

    def test_screens_present(self):
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        assert len(pack.screens) == 3
        screen_ids = [s.id for s in pack.screens]
        assert "scr_login" in screen_ids
        assert "scr_dashboard" in screen_ids
        assert "scr_profile" in screen_ids

    def test_screens_have_purpose(self):
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        for screen in pack.screens:
            assert screen.purpose, f"Screen {screen.id} missing purpose"

    def test_screens_have_elements(self):
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        for screen in pack.screens:
            assert len(screen.elements) > 0, f"Screen {screen.id} has no elements"

    def test_transitions_present(self):
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        assert len(pack.transitions) >= 2

    def test_journey_present(self):
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        assert len(pack.journeys) >= 1
        assert pack.journeys[0].name == "Main Exploration"

    def test_scan_metadata(self):
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        assert pack.scan_metadata.screens_discovered == 3
        assert pack.scan_metadata.transitions_discovered >= 2

    def test_pack_size_calculated(self):
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        assert pack.scan_metadata.pack_size_bytes > 0

    def test_app_metadata_has_package(self):
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        assert pack.app_metadata.get("package_name") == "com.revrag.targetapp"

    def test_design_tokens_placeholder(self):
        """Design tokens should exist (even as empty placeholders for Slaven)."""
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        for screen in pack.screens:
            assert screen.design_tokens is not None

    def test_forms_extracted(self):
        """Screens with text_input elements should have forms."""
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        login = next(s for s in pack.screens if s.id == "scr_login")
        assert len(login.forms) >= 1


# ── Test: Stability ──────────────────────────────────────────────────

class TestPackStability:
    """Same session data must produce identical packs."""

    def test_same_session_same_pack_structure(self):
        """Two builds from the same session should match structurally."""
        session = _build_session_with_screens()
        pack1 = build_knowledge_pack(session)
        pack2 = build_knowledge_pack(session)

        assert len(pack1.screens) == len(pack2.screens)
        assert len(pack1.transitions) == len(pack2.transitions)

        # Screen IDs should be in the same order
        ids1 = [s.id for s in pack1.screens]
        ids2 = [s.id for s in pack2.screens]
        assert ids1 == ids2

    def test_stable_screen_ordering(self):
        """Screens should be sorted by ID for clean diffs."""
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        ids = [s.id for s in pack.screens]
        assert ids == sorted(ids)

    def test_stable_transition_ordering(self):
        """Transitions should be sorted by (from, to)."""
        session = _build_session_with_screens()
        pack = build_knowledge_pack(session)
        pairs = [(t.from_screen, t.to_screen) for t in pack.transitions]
        assert pairs == sorted(pairs)


# ── Test: Endpoints ──────────────────────────────────────────────────

class TestPackEndpoints:
    """HTTP endpoint tests for GET /knowledge-pack and POST /finalize."""

    def test_get_unknown_session_404(self, client):
        response = client.get("/knowledge-pack/nonexistent")
        assert response.status_code == 404

    def test_finalize_unknown_session_404(self, client):
        response = client.post("/finalize?session_id=nonexistent")
        assert response.status_code == 404

    def test_ingest_then_get_pack(self, client, sample_observation):
        """After ingesting screens, GET should return a pack."""
        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "pack-endpoint-test"

        # Ingest a screen
        client.post("/ingest-screen", json=obs)

        # Get the pack
        response = client.get(f"/knowledge-pack/{obs['session_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "1.0"
        assert len(data["screens"]) >= 1

    def test_ingest_then_finalize(self, client, sample_observation):
        """After ingesting, finalize should produce a complete pack."""
        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "finalize-endpoint-test"

        client.post("/ingest-screen", json=obs)
        obs["step"] = 1
        client.post("/ingest-screen", json=obs)

        response = client.post(f"/finalize?session_id={obs['session_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["scan_metadata"]["screens_discovered"] >= 1
        assert data["scan_metadata"]["pack_size_bytes"] > 0
