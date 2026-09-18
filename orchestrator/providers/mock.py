"""Mock LLM provider — deterministic, no network, no API key.

Returns pre-defined responses based on UI tree heuristics so the full
pipeline can be tested end-to-end without a real model.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from orchestrator.providers.base import LLMProvider, ScreenAnalysis


class MockLLMProvider(LLMProvider):
    """Deterministic mock that inspects the UI tree to produce responses."""

    @property
    def name(self) -> str:
        return "mock"

    async def analyse_screen(
        self,
        screenshot_b64: str,
        ui_tree: dict[str, Any],
        exploration_context: Optional[dict[str, Any]] = None,
    ) -> ScreenAnalysis:
        """Analyse a screen using simple heuristic rules on the UI tree."""

        root = ui_tree.get("root", {})
        activity = ui_tree.get("activity_name", "UnknownActivity")

        # Collect all leaf elements
        flat_elements = self._flatten_tree(root)

        # Build structured elements
        elements = []
        for i, el in enumerate(flat_elements):
            el_id = f"el_{i:02d}"
            role = self._infer_role(el)
            label = (
                el.get("text")
                or el.get("content_description")
                or el.get("class_name", "unknown").split(".")[-1]
            )
            bounds = el.get("bounds", [0, 0, 0, 0])
            actions = self._infer_actions(el, role)

            elements.append({
                "id": el_id,
                "role": role,
                "label": label,
                "bounds": bounds,
                "actions": actions,
            })

        # Determine screen purpose from activity name and visible text
        purpose = self._infer_purpose(activity, flat_elements)

        # Build candidate actions — one per interactive element
        candidate_actions = []
        for el_info in elements:
            if el_info["actions"]:
                action_type = el_info["actions"][0]
                value = "9876543210" if action_type == "type_text" else None
                candidate_actions.append({
                    "type": action_type,
                    "target_element_id": el_info["id"],
                    "value": value,
                    "reason": f"Unexplored {el_info['role']}: {el_info['label']}",
                    "confidence": 0.85,
                })

        # Select next action — pick first unexplored interactive element
        context = exploration_context or {}
        attempted = set(context.get("attempted_actions", []))

        next_action: dict[str, Any] = {
            "type": "null",
            "reason": "No unexplored actions remain",
            "confidence": 1.0,
        }

        for ca in candidate_actions:
            action_key = f"{ca['type']}:{ca['target_element_id']}"
            if action_key not in attempted:
                next_action = dict(ca)
                next_action["confidence"] = 0.90
                break

        return ScreenAnalysis(
            screen_purpose=purpose,
            elements=elements,
            candidate_actions=candidate_actions,
            next_action=next_action,
            confidence=next_action.get("confidence", 0.0),
            raw_text=json.dumps({
                "provider": "mock",
                "activity": activity,
                "element_count": len(elements),
            }),
        )

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _flatten_tree(node: dict[str, Any]) -> list[dict[str, Any]]:
        """Recursively collect leaf nodes (or interactive nodes)."""
        result: list[dict[str, Any]] = []
        children = node.get("children", [])
        if not children:
            result.append(node)
        else:
            # Include this node if it's interactive
            if node.get("clickable") or node.get("editable"):
                result.append(node)
            for child in children:
                result.extend(MockLLMProvider._flatten_tree(child))
        return result

    @staticmethod
    def _infer_role(el: dict[str, Any]) -> str:
        """Map Android class name + flags to a semantic role."""
        cls = el.get("class_name", "").lower()
        if "edittext" in cls or el.get("editable"):
            return "text_input"
        if "button" in cls:
            return "button"
        if "imageview" in cls:
            return "image"
        if "checkbox" in cls:
            return "checkbox"
        if "switch" in cls or "toggle" in cls:
            return "toggle"
        if "spinner" in cls:
            return "dropdown"
        if "recyclerview" in cls or "listview" in cls:
            return "list"
        if "textview" in cls:
            return "label"
        if el.get("clickable"):
            return "button"
        return "label"

    @staticmethod
    def _infer_actions(el: dict[str, Any], role: str) -> list[str]:
        """Determine what actions are possible on an element."""
        actions: list[str] = []
        if role == "text_input":
            actions.append("type_text")
        if el.get("clickable") or role in ("button", "checkbox", "toggle", "dropdown"):
            actions.append("tap")
        if role == "list":
            actions.append("scroll")
        return actions

    @staticmethod
    def _infer_purpose(activity: str, elements: list[dict[str, Any]]) -> str:
        """Guess screen purpose from activity name and visible text."""
        act_lower = activity.lower()

        # Collect all visible text
        texts = [
            el.get("text", "")
            for el in elements
            if el.get("text")
        ]
        text_blob = " ".join(texts).lower()

        if "login" in act_lower or "otp" in text_blob or "sign in" in text_blob:
            return "User authentication / login screen"
        if "dashboard" in act_lower or "home" in act_lower:
            return "Main dashboard showing key app sections"
        if "profile" in act_lower:
            return "User profile screen"
        if "kyc" in act_lower or "form" in act_lower:
            return "Data entry form for user information"
        if "settings" in act_lower:
            return "Application settings and preferences"
        if "feed" in act_lower:
            return "Scrollable content feed"
        if "detail" in act_lower:
            return "Detail view for a selected item"

        return f"Screen: {activity.split('.')[-1] if '.' in activity else activity}"
