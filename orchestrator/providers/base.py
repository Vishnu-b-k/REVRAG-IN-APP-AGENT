"""Abstract LLM provider interface.

All model providers (mock, Gemini, OpenAI, etc.) must implement this
interface so the rest of the codebase never depends on a specific SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


class LLMProviderError(Exception):
    """Raised when the LLM provider fails irrecoverably for one call."""


@dataclass
class ScreenAnalysis:
    """Structured output from the LLM provider for one screen observation.

    This is the *raw* provider output before normalisation into our
    internal ``IngestScreenResponse`` model.  Fields use plain Python
    types so providers don't need to import Pydantic models.
    """

    screen_purpose: str = ""
    elements: list[dict[str, Any]] = field(default_factory=list)
    candidate_actions: list[dict[str, Any]] = field(default_factory=list)
    next_action: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    raw_text: str = ""  # raw model output for debugging / logging


class LLMProvider(ABC):
    """Base class every model adapter must extend."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name (e.g. 'mock', 'gemini-2.0-flash')."""

    @abstractmethod
    async def analyse_screen(
        self,
        screenshot_b64: str,
        ui_tree: dict[str, Any],
        exploration_context: Optional[dict[str, Any]] = None,
    ) -> ScreenAnalysis:
        """Analyse a screen observation and return structured understanding.

        Parameters
        ----------
        screenshot_b64:
            Base64-encoded PNG screenshot.
        ui_tree:
            Serialised accessibility tree (dict form of ``UITree``).
        exploration_context:
            Optional dict with session state, visited screens, attempted
            actions, etc.  Providers may use this to avoid revisiting
            completed branches.

        Returns
        -------
        ScreenAnalysis with purpose, elements, candidate actions, and
        selected next action.

        Raises
        ------
        LLMProviderError
            If the provider cannot produce a valid result after retries.
        """
