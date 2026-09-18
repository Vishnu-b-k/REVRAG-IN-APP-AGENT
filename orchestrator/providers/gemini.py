"""Gemini multimodal LLM provider.

Sends screenshot_b64 + serialised UI tree to Gemini via the REST API
and parses the structured JSON response.

Falls back to MockLLMProvider if the model returns malformed output.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

from orchestrator.providers.base import LLMProvider, LLMProviderError, ScreenAnalysis

logger = logging.getLogger(__name__)

# ── Structured prompt template ───────────────────────────────────────

SYSTEM_PROMPT = """You are an Android app exploration agent. You analyse screenshots and UI accessibility trees to understand screen content and decide the next exploration action.

You MUST respond with valid JSON only — no markdown, no explanation, no code fences.

Respond with this exact JSON structure:
{
  "screen_purpose": "Brief description of what this screen is for",
  "elements": [
    {
      "id": "el_00",
      "role": "button|text_input|label|image|checkbox|toggle|dropdown|list",
      "label": "Human-readable label",
      "bounds": [left, top, right, bottom],
      "actions": ["tap", "type_text", "scroll"]
    }
  ],
  "candidate_actions": [
    {
      "type": "tap|type_text|scroll|back|null",
      "target_element_id": "el_00",
      "value": "text to type (only for type_text)",
      "reason": "Why this action advances exploration",
      "confidence": 0.85
    }
  ],
  "next_action": {
    "type": "tap|type_text|scroll|back|null",
    "target_element_id": "el_00",
    "value": null,
    "reason": "Why this is the best next action",
    "confidence": 0.90
  }
}

Rules:
- Identify ALL interactive elements (buttons, inputs, links, toggles).
- Rank candidate_actions by exploration value — prefer unexplored interactive elements.
- For type_text, provide realistic test data (e.g., "9876543210" for phone, "Test User" for name).
- Set confidence 0.0-1.0 based on how certain you are the action will succeed.
- If the screen has no unexplored actions, set next_action.type to "null".
- Use "back" when the current screen is fully explored and you need to return."""

USER_PROMPT_TEMPLATE = """Analyse this Android screen and decide the next exploration action.

Activity: {activity_name}
Package: {package_name}

UI Accessibility Tree:
{ui_tree_json}

{context_section}

Respond with valid JSON only."""


class GeminiProvider(LLMProvider):
    """Gemini multimodal provider using the REST API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        if not api_key:
            raise LLMProviderError("Gemini API key is required. Set LLM_API_KEY in .env")

        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

    @property
    def name(self) -> str:
        return f"gemini:{self._model}"

    async def analyse_screen(
        self,
        screenshot_b64: str,
        ui_tree: dict[str, Any],
        exploration_context: Optional[dict[str, Any]] = None,
    ) -> ScreenAnalysis:
        """Send screenshot + UI tree to Gemini and parse the response."""

        # Build the text prompt
        context_section = ""
        if exploration_context:
            ctx = exploration_context
            context_section = (
                f"Exploration context:\n"
                f"- Session: {ctx.get('session_id', 'unknown')}\n"
                f"- Step: {ctx.get('current_step', 0)}\n"
                f"- Screens visited: {ctx.get('screens_visited', [])}\n"
                f"- Actions attempted: {ctx.get('attempted_actions', [])}\n"
            )

        # Compact UI tree (remove screenshot-level data for the text portion)
        tree_compact = {
            "package_name": ui_tree.get("package_name", ""),
            "activity_name": ui_tree.get("activity_name", ""),
            "root": ui_tree.get("root", {}),
        }
        ui_tree_json = json.dumps(tree_compact, indent=2, default=str)

        user_text = USER_PROMPT_TEMPLATE.format(
            activity_name=ui_tree.get("activity_name", "Unknown"),
            package_name=ui_tree.get("package_name", "Unknown"),
            ui_tree_json=ui_tree_json,
            context_section=context_section,
        )

        # Build the Gemini API request
        request_body = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": screenshot_b64,
                            }
                        },
                        {"text": user_text},
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
                "maxOutputTokens": 4096,
            },
        }

        url = f"{self._base_url}/models/{self._model}:generateContent?key={self._api_key}"

        # Call the API with retries
        last_error: Optional[Exception] = None
        raw_text = ""

        for attempt in range(1, self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        url,
                        json=request_body,
                        headers={"Content-Type": "application/json"},
                    )

                if response.status_code != 200:
                    error_body = response.text[:500]
                    logger.warning(
                        "Gemini API error (attempt %d/%d): %d %s",
                        attempt, self._max_retries, response.status_code, error_body,
                    )
                    last_error = LLMProviderError(
                        f"Gemini API returned {response.status_code}: {error_body}"
                    )
                    continue

                # Parse the response
                resp_data = response.json()
                raw_text = self._extract_text(resp_data)

                # Parse the JSON from the model output
                analysis = self._parse_response(raw_text)
                return analysis

            except httpx.TimeoutException as exc:
                logger.warning("Gemini timeout (attempt %d/%d): %s", attempt, self._max_retries, exc)
                last_error = exc
            except json.JSONDecodeError as exc:
                logger.warning("Gemini JSON parse error (attempt %d/%d): %s", attempt, self._max_retries, exc)
                last_error = exc
            except Exception as exc:
                logger.warning("Gemini unexpected error (attempt %d/%d): %s", attempt, self._max_retries, exc)
                last_error = exc

        # All retries exhausted
        raise LLMProviderError(
            f"Gemini provider failed after {self._max_retries} attempts: {last_error}"
        )

    # ── Response parsing ─────────────────────────────────────────────

    @staticmethod
    def _extract_text(resp_data: dict[str, Any]) -> str:
        """Extract text content from Gemini API response structure."""
        try:
            candidates = resp_data.get("candidates", [])
            if not candidates:
                raise LLMProviderError("No candidates in Gemini response")

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                raise LLMProviderError("No parts in Gemini response")

            return parts[0].get("text", "")
        except (IndexError, KeyError) as exc:
            raise LLMProviderError(f"Unexpected Gemini response structure: {exc}")

    @staticmethod
    def _parse_response(raw_text: str) -> ScreenAnalysis:
        """Parse the model's JSON text into a ScreenAnalysis."""

        # Strip any markdown code fences the model might have added
        clean = raw_text.strip()
        if clean.startswith("```"):
            # Remove opening fence
            first_newline = clean.index("\n") if "\n" in clean else len(clean)
            clean = clean[first_newline + 1:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

        data = json.loads(clean)

        return ScreenAnalysis(
            screen_purpose=data.get("screen_purpose", ""),
            elements=data.get("elements", []),
            candidate_actions=data.get("candidate_actions", []),
            next_action=data.get("next_action", {"type": "null", "confidence": 0.0}),
            confidence=data.get("next_action", {}).get("confidence", 0.0),
            raw_text=raw_text,
        )
