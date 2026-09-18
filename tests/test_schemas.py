"""Tests for Pydantic request/response/knowledge-pack schemas."""

import json

import pytest
from pydantic import ValidationError

from orchestrator.models import (
    ObservationRequest,
    IngestScreenResponse,
    NextAction,
    ActionType,
    ScreenElement,
    KnowledgePack,
    Screen,
    Transition,
    DesignTokens,
    ScanMetadata,
)


# ─── ObservationRequest ──────────────────────────────────────────────

class TestObservationRequest:
    """Validate the /ingest-screen request model."""

    def test_valid_fixture_parses(self, sample_observation):
        """The sample fixture should parse without errors."""
        obs = ObservationRequest(**sample_observation)
        assert obs.session_id == "demo-session-001"
        assert obs.step == 0
        assert obs.ui_tree.package_name == "com.revrag.targetapp"
        assert obs.previous_state_id is None

    def test_fixture_tree_has_children(self, sample_observation):
        """The tree should have nested children."""
        obs = ObservationRequest(**sample_observation)
        root = obs.ui_tree.root
        assert len(root.children) > 0
        # Login screen has a LinearLayout with 5 children
        linear = root.children[0]
        assert len(linear.children) == 5

    def test_missing_session_id_fails(self, sample_observation):
        """session_id is required."""
        bad = {**sample_observation, "session_id": ""}
        with pytest.raises(ValidationError):
            ObservationRequest(**bad)

    def test_missing_screenshot_fails(self, sample_observation):
        """screenshot_b64 is required."""
        bad = {**sample_observation, "screenshot_b64": ""}
        with pytest.raises(ValidationError):
            ObservationRequest(**bad)

    def test_negative_step_fails(self, sample_observation):
        """step must be >= 0."""
        bad = {**sample_observation, "step": -1}
        with pytest.raises(ValidationError):
            ObservationRequest(**bad)


# ─── IngestScreenResponse ────────────────────────────────────────────

class TestIngestScreenResponse:
    """Validate the /ingest-screen response model."""

    def test_valid_response(self):
        """A complete response should parse."""
        resp = IngestScreenResponse(
            screen_id="scr_01",
            state_id="state_01",
            is_new_screen=True,
            description="Login screen with phone input",
            elements=[
                ScreenElement(
                    id="el_01",
                    role="text_input",
                    label="Phone number",
                    bounds=[100, 700, 880, 100],
                    actions=["type_text"],
                )
            ],
            candidate_actions=[],
            next_action=NextAction(
                type=ActionType.TYPE_TEXT,
                target_element_id="el_01",
                value="9876543210",
                reason="Unexplored required field",
                confidence=0.92,
            ),
        )
        assert resp.screen_id == "scr_01"
        assert resp.next_action.type == ActionType.TYPE_TEXT

    def test_null_action_for_completion(self):
        """null action means exploration is done."""
        resp = IngestScreenResponse(
            screen_id="scr_99",
            state_id="state_99",
            is_new_screen=False,
            description="Already visited",
            next_action=NextAction(
                type=ActionType.NULL,
                reason="Exploration complete",
            ),
        )
        assert resp.next_action.type == ActionType.NULL

    def test_invalid_action_type_rejected(self):
        """An unknown action type should be rejected."""
        with pytest.raises(ValidationError):
            NextAction(
                type="swipe_left",  # not in ActionType
                reason="bad",
            )

    def test_confidence_bounds(self):
        """confidence must be 0.0–1.0."""
        with pytest.raises(ValidationError):
            NextAction(type=ActionType.TAP, confidence=1.5)
        with pytest.raises(ValidationError):
            NextAction(type=ActionType.TAP, confidence=-0.1)


# ─── KnowledgePack ───────────────────────────────────────────────────

class TestKnowledgePack:
    """Validate the knowledge pack schema."""

    def test_empty_pack(self):
        """A minimal empty pack should be valid."""
        pack = KnowledgePack()
        assert pack.schema_version == "1.0"
        assert pack.screens == []
        assert pack.transitions == []

    def test_pack_with_screen(self):
        """Pack with one screen should serialize cleanly."""
        pack = KnowledgePack(
            screens=[
                Screen(
                    id="scr_01",
                    fingerprint="abc123",
                    name="Login",
                    purpose="User authentication via phone OTP",
                    elements=[
                        {"id": "el_01", "role": "text_input", "label": "Phone"}
                    ],
                    design_tokens=DesignTokens(
                        dominant_colors=["#1A1A2E", "#E94560"],
                        mode="dark",
                    ),
                )
            ],
            scan_metadata=ScanMetadata(
                total_steps=12,
                screens_discovered=4,
                transitions_discovered=5,
            ),
        )
        assert len(pack.screens) == 1
        assert pack.screens[0].design_tokens.mode == "dark"
        assert pack.scan_metadata.screens_discovered == 4

    def test_transition_model(self):
        """Transitions use from/to aliases."""
        t = Transition(**{"from": "scr_01", "to": "scr_02", "action": {"type": "tap"}})
        assert t.from_screen == "scr_01"
        assert t.to_screen == "scr_02"

    def test_pack_roundtrip_json(self):
        """Pack should serialize to JSON and back."""
        pack = KnowledgePack(
            app_metadata={"name": "RevRag Target App", "package": "com.revrag.targetapp"},
            screens=[
                Screen(id="scr_01", name="Login", purpose="Auth"),
            ],
        )
        json_str = pack.model_dump_json()
        loaded = KnowledgePack.model_validate_json(json_str)
        assert loaded.screens[0].id == "scr_01"
