"""Tests for POST /ingest-screen endpoint and the full ingestion pipeline."""

import json
import copy

import pytest

from orchestrator.models.action import ActionType


class TestIngestScreenEndpoint:
    """Tests for the /ingest-screen HTTP endpoint."""

    def test_valid_fixture_returns_200(self, client, sample_observation):
        """A valid observation fixture should return 200 with typed response."""
        response = client.post("/ingest-screen", json=sample_observation)
        assert response.status_code == 200

        data = response.json()
        assert "screen_id" in data
        assert "state_id" in data
        assert "is_new_screen" in data
        assert "description" in data
        assert "elements" in data
        assert "candidate_actions" in data
        assert "next_action" in data

    def test_response_has_valid_next_action(self, client, sample_observation):
        """The next_action must have a valid ActionType."""
        response = client.post("/ingest-screen", json=sample_observation)
        data = response.json()

        action = data["next_action"]
        assert action["type"] in [a.value for a in ActionType]
        assert "reason" in action
        assert 0.0 <= action["confidence"] <= 1.0

    def test_elements_have_required_fields(self, client, sample_observation):
        """Each element in the response must have id, role, label, bounds."""
        response = client.post("/ingest-screen", json=sample_observation)
        data = response.json()

        for el in data["elements"]:
            assert "id" in el
            assert "role" in el
            assert "label" in el
            assert "bounds" in el

    def test_first_observation_is_new_screen(self, client, sample_observation):
        """The first observation in a new session should be is_new_screen=True."""
        # Use a unique session to avoid state bleed between tests
        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "test-new-screen-session"

        response = client.post("/ingest-screen", json=obs)
        data = response.json()
        assert data["is_new_screen"] is True

    def test_repeated_observation_not_new(self, client, sample_observation):
        """The same screen sent twice should eventually return is_new_screen=False."""
        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "test-repeat-session"

        # First request
        r1 = client.post("/ingest-screen", json=obs)
        assert r1.json()["is_new_screen"] is True

        # Second request (same tree, different step)
        obs["step"] = 1
        r2 = client.post("/ingest-screen", json=obs)
        assert r2.json()["is_new_screen"] is False

    def test_missing_session_id_returns_422(self, client, sample_observation):
        """Missing required field should return 422."""
        bad = copy.deepcopy(sample_observation)
        bad.pop("session_id")
        response = client.post("/ingest-screen", json=bad)
        assert response.status_code == 422

    def test_missing_screenshot_returns_422(self, client, sample_observation):
        """Missing screenshot should return 422."""
        bad = copy.deepcopy(sample_observation)
        bad.pop("screenshot_b64")
        response = client.post("/ingest-screen", json=bad)
        assert response.status_code == 422

    def test_missing_ui_tree_returns_422(self, client, sample_observation):
        """Missing ui_tree should return 422."""
        bad = copy.deepcopy(sample_observation)
        bad.pop("ui_tree")
        response = client.post("/ingest-screen", json=bad)
        assert response.status_code == 422

    def test_empty_body_returns_422(self, client):
        """Empty JSON body should return 422."""
        response = client.post("/ingest-screen", json={})
        assert response.status_code == 422


class TestMockProviderDeterminism:
    """Verify the mock provider returns identical results for identical input."""

    def test_same_input_same_output(self, client, sample_observation):
        """Two identical requests should produce the same screen analysis."""
        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "determinism-test-a"

        r1 = client.post("/ingest-screen", json=obs)

        obs["session_id"] = "determinism-test-b"
        r2 = client.post("/ingest-screen", json=obs)

        d1, d2 = r1.json(), r2.json()

        # Screen IDs should match (same activity → same naive screen ID)
        assert d1["screen_id"] == d2["screen_id"]
        # Descriptions should match
        assert d1["description"] == d2["description"]
        # Element count should match
        assert len(d1["elements"]) == len(d2["elements"])

    def test_login_screen_detected(self, client, sample_observation):
        """Mock provider should detect the login screen purpose."""
        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "login-detect-test"

        response = client.post("/ingest-screen", json=obs)
        data = response.json()

        assert "login" in data["description"].lower() or "auth" in data["description"].lower()


class TestEventLogging:
    """Verify events are recorded in the session."""

    def test_events_recorded_after_ingest(self, client, sample_observation):
        """After ingestion, the session should have observation + model_response events."""
        from orchestrator.services.session import session_store

        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "event-log-test"

        client.post("/ingest-screen", json=obs)

        session = session_store.get(obs["session_id"])
        assert session is not None

        event_types = [e.event_type.value for e in session.events]
        assert "session_start" in event_types
        assert "observation" in event_types
        assert "model_response" in event_types

    def test_multiple_steps_accumulate_events(self, client, sample_observation):
        """Each step should add events to the log."""
        from orchestrator.services.session import session_store

        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "multi-step-test"

        client.post("/ingest-screen", json=obs)
        obs["step"] = 1
        client.post("/ingest-screen", json=obs)
        obs["step"] = 2
        client.post("/ingest-screen", json=obs)

        session = session_store.get(obs["session_id"])
        assert session is not None
        # session_start + 3*(observation + model_response) = 7 events
        assert len(session.events) >= 7


class TestMalformedModelOutput:
    """Ensure malformed model output is safely handled."""

    def test_invalid_action_type_normalised_to_null(self):
        """If the provider returns a bad action type, normalisation falls back to null."""
        from orchestrator.services.screen_ingestion import _normalise_next_action

        raw = {"type": "swipe_diagonal", "confidence": 0.5}
        result = _normalise_next_action(raw)
        assert result.type == ActionType.NULL
        assert result.confidence == 0.0

    def test_missing_type_normalised_to_null(self):
        """If the action dict has no 'type' key, fall back to null."""
        from orchestrator.services.screen_ingestion import _normalise_next_action

        result = _normalise_next_action({"reason": "oops"})
        assert result.type == ActionType.NULL

    def test_confidence_clamped(self):
        """Confidence outside 0–1 should be clamped."""
        from orchestrator.services.screen_ingestion import _normalise_next_action

        result = _normalise_next_action({"type": "tap", "confidence": 5.0})
        assert result.confidence == 1.0

        result2 = _normalise_next_action({"type": "tap", "confidence": -2.0})
        assert result2.confidence == 0.0

    def test_invalid_candidates_dropped(self):
        """Invalid candidate actions should be silently dropped."""
        from orchestrator.services.screen_ingestion import _normalise_candidates

        raw = [
            {"type": "tap", "target_element_id": "el_01", "confidence": 0.9},  # valid
            {"type": "fly_away", "confidence": 0.5},  # invalid type
            {"no_type_key": True},  # missing type
        ]
        result = _normalise_candidates(raw)
        assert len(result) == 1
        assert result[0].type == ActionType.TAP
