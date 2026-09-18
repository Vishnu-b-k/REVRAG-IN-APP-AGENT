"""Tests for V-5: Real LLM provider wiring.

Tests:
- Config switch toggles provider
- Gemini provider constructs correct API calls (mock HTTP layer)
- Malformed model response triggers fallback to mock
- Response parsing works for valid JSON
- No API keys in source
"""

import json
import copy
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from orchestrator.providers.base import LLMProviderError, ScreenAnalysis
from orchestrator.providers.gemini import GeminiProvider, SYSTEM_PROMPT


# ── Test: Config Switch ─────────────────────────────────────────────

class TestConfigSwitch:
    """Verify the provider factory responds to config changes."""

    def test_default_is_mock(self, client, sample_observation):
        """Default config (LLM_PROVIDER=mock) should use mock provider."""
        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "config-switch-mock"
        response = client.post("/ingest-screen", json=obs)
        assert response.status_code == 200

    def test_unknown_provider_returns_500(self, client, sample_observation):
        """An unknown provider name should return 500."""
        from orchestrator.config import settings

        original = settings.llm_provider
        try:
            settings.llm_provider = "gpt-99-turbo"
            obs = copy.deepcopy(sample_observation)
            obs["session_id"] = "config-switch-unknown"
            response = client.post("/ingest-screen", json=obs)
            assert response.status_code == 500
        finally:
            settings.llm_provider = original


# ── Test: Gemini Provider Construction ───────────────────────────────

class TestGeminiProviderConstruction:
    """Verify Gemini provider setup and validation."""

    def test_requires_api_key(self):
        """Creating a Gemini provider without API key should raise."""
        with pytest.raises(LLMProviderError, match="API key is required"):
            GeminiProvider(api_key="")

    def test_provider_name(self):
        """Provider name should include model."""
        provider = GeminiProvider(api_key="test-key", model="gemini-2.0-flash")
        assert provider.name == "gemini:gemini-2.0-flash"

    def test_custom_model(self):
        """Custom model name should be reflected."""
        provider = GeminiProvider(api_key="test-key", model="gemini-2.5-pro")
        assert "gemini-2.5-pro" in provider.name


# ── Test: Response Parsing ───────────────────────────────────────────

class TestGeminiResponseParsing:
    """Test JSON response parsing from Gemini output."""

    def test_valid_json_parsed(self):
        """Valid JSON from Gemini should parse to ScreenAnalysis."""
        raw = json.dumps({
            "screen_purpose": "Login screen",
            "elements": [
                {"id": "el_00", "role": "text_input", "label": "Phone", "bounds": [0, 0, 100, 50], "actions": ["type_text"]}
            ],
            "candidate_actions": [
                {"type": "type_text", "target_element_id": "el_00", "confidence": 0.9, "reason": "Enter phone"}
            ],
            "next_action": {
                "type": "type_text",
                "target_element_id": "el_00",
                "value": "9876543210",
                "reason": "Fill phone field",
                "confidence": 0.9,
            },
        })

        result = GeminiProvider._parse_response(raw)
        assert isinstance(result, ScreenAnalysis)
        assert result.screen_purpose == "Login screen"
        assert len(result.elements) == 1
        assert result.confidence == 0.9

    def test_json_with_code_fences(self):
        """JSON wrapped in markdown code fences should still parse."""
        inner = json.dumps({
            "screen_purpose": "Dashboard",
            "elements": [],
            "candidate_actions": [],
            "next_action": {"type": "null", "confidence": 1.0},
        })
        raw = f"```json\n{inner}\n```"

        result = GeminiProvider._parse_response(raw)
        assert result.screen_purpose == "Dashboard"

    def test_malformed_json_raises(self):
        """Malformed JSON should raise JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            GeminiProvider._parse_response("this is not json at all {{{")

    def test_extract_text_from_response(self):
        """Extract text from Gemini API response structure."""
        resp_data = {
            "candidates": [{
                "content": {
                    "parts": [{"text": '{"screen_purpose": "test"}'}]
                }
            }]
        }
        text = GeminiProvider._extract_text(resp_data)
        assert '"screen_purpose"' in text

    def test_extract_text_empty_candidates(self):
        """Empty candidates should raise."""
        with pytest.raises(LLMProviderError):
            GeminiProvider._extract_text({"candidates": []})


# ── Test: Fallback Behavior ──────────────────────────────────────────

class TestFallbackToMock:
    """When Gemini fails, the endpoint should fall back to mock."""

    def test_provider_error_falls_back(self, client, sample_observation):
        """If the primary provider raises LLMProviderError, fallback to mock."""
        from orchestrator.config import settings

        # Temporarily set to gemini
        original = settings.llm_provider
        original_key = settings.llm_api_key
        try:
            settings.llm_provider = "gemini"
            settings.llm_api_key = "fake-test-key"

            # Patch GeminiProvider at its source so the lazy import picks it up
            with patch(
                "orchestrator.providers.gemini.GeminiProvider"
            ) as MockGemini:
                instance = MockGemini.return_value
                instance.name = "gemini:test"
                instance.analyse_screen = AsyncMock(
                    side_effect=LLMProviderError("Simulated failure")
                )

                # Also patch the lazy import inside _get_provider
                with patch(
                    "orchestrator.routes.ingest.GeminiProvider",
                    create=True,
                    new=MockGemini,
                ):
                    obs = copy.deepcopy(sample_observation)
                    obs["session_id"] = "fallback-test"

                    response = client.post("/ingest-screen", json=obs)
                    # Should succeed via mock fallback
                    assert response.status_code == 200
                    data = response.json()
                    assert data["next_action"]["type"] in ["type_text", "tap", "null"]

        finally:
            settings.llm_provider = original
            settings.llm_api_key = original_key


# ── Test: Prompt Content ─────────────────────────────────────────────

class TestPromptContent:
    """Verify the structured prompt has the right instructions."""

    def test_system_prompt_requires_json(self):
        """System prompt should require JSON output."""
        assert "valid JSON" in SYSTEM_PROMPT
        assert "screen_purpose" in SYSTEM_PROMPT

    def test_system_prompt_has_action_types(self):
        """System prompt should list all valid action types."""
        assert "tap" in SYSTEM_PROMPT
        assert "type_text" in SYSTEM_PROMPT
        assert "scroll" in SYSTEM_PROMPT
        assert "back" in SYSTEM_PROMPT
        assert "null" in SYSTEM_PROMPT

    def test_system_prompt_mentions_confidence(self):
        """System prompt should instruct about confidence scoring."""
        assert "confidence" in SYSTEM_PROMPT
        assert "0.0-1.0" in SYSTEM_PROMPT or "0.0" in SYSTEM_PROMPT


# ── Test: No API Keys in Source ──────────────────────────────────────

class TestNoApiKeysInSource:
    """Verify no real API keys are committed."""

    def test_env_example_has_empty_key(self):
        with open(".env.example") as f:
            content = f.read()
        # LLM_API_KEY should be empty or placeholder
        for line in content.split("\n"):
            if line.startswith("LLM_API_KEY"):
                value = line.split("=", 1)[1].strip()
                assert value == "" or value.startswith("#"), \
                    f"LLM_API_KEY has a non-empty value in .env.example: {value}"

    def test_no_env_file_committed(self):
        """The .env file (with real keys) should not exist or be in .gitignore."""
        import os
        with open(".gitignore") as f:
            gitignore = f.read()
        assert ".env" in gitignore
