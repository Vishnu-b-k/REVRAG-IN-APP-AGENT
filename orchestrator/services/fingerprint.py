"""Stable screen fingerprinting and deduplication.

Canonicalises the UI tree to remove volatile values (OTP codes, timestamps,
user text, changing counters, session IDs) while preserving structural layout,
semantic roles, and interaction types.  Produces a deterministic fingerprint
so the same logical screen always gets the same screen ID.

Phase V-3 of the execution plan.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Optional


# ── Volatile-value patterns ──────────────────────────────────────────

# Match common volatile text: OTP digits, timestamps, prices, counters, UUIDs
_VOLATILE_PATTERNS: list[tuple[re.Pattern, str]] = [
    # OTP / verification codes (4-8 digits alone)
    (re.compile(r"^\d{4,8}$"), "<OTP>"),
    # Timestamps: HH:MM, HH:MM:SS, dates
    (re.compile(r"\d{1,2}:\d{2}(:\d{2})?(\s*(AM|PM|am|pm))?"), "<TIME>"),
    (re.compile(r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}"), "<DATE>"),
    # Prices: $12.34, ₹1,234, etc.
    (re.compile(r"[$₹€£¥]\s*[\d,]+\.?\d*"), "<PRICE>"),
    (re.compile(r"[\d,]+\.?\d*\s*[$₹€£¥]"), "<PRICE>"),
    # Phone numbers (7+ digits with optional formatting)
    (re.compile(r"[\+\d][\d\s\-\(\)]{6,}"), "<PHONE>"),
    # UUIDs
    (re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I), "<UUID>"),
    # Email addresses
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "<EMAIL>"),
    # Common greeting patterns with names (handles commas, extra words, names)
    (re.compile(r"(Hi|Hello|Welcome|Dear)\b[\w,\s]*", re.I), "<GREETING>"),
    # Standalone numbers (counters, IDs, badges) — any length
    (re.compile(r"(?<!\w)\d+(?!\w)"), "<NUM>"),
]

# Coordinate bucket size (pixels) — small shifts don't change identity
_COORD_BUCKET_SIZE = 50


def normalise_volatile_text(text: Optional[str]) -> Optional[str]:
    """Replace volatile substrings with stable placeholders.

    Returns None if text is None.  Returns the normalised string otherwise.
    """
    if text is None:
        return None

    result = text.strip()

    for pattern, replacement in _VOLATILE_PATTERNS:
        result = pattern.sub(replacement, result)

    # Collapse whitespace
    result = re.sub(r"\s+", " ", result).strip()

    return result


def normalise_bounds(bounds: list[int], bucket_size: int = _COORD_BUCKET_SIZE) -> list[int]:
    """Bucket pixel coordinates so small shifts don't change the fingerprint.

    [left, top, right, bottom] → bucketed values.
    """
    if len(bounds) != 4:
        return bounds
    return [
        (v // bucket_size) * bucket_size
        for v in bounds
    ]


def canonicalise_element(element: dict[str, Any]) -> dict[str, Any]:
    """Produce a canonical representation of one UI element.

    Preserves:
    - class_name (widget type / role)
    - semantic labels (content_description — normalised)
    - interaction flags (clickable, editable, etc.)
    - bucketed bounds (relative layout structure)

    Removes / normalises:
    - Volatile text (OTP, phone, timestamps, etc.)
    - Exact pixel coordinates
    """
    is_editable = element.get("editable", False)
    cls_name = element.get("class_name", "").split(".")[-1].lower()

    # For editable fields, the text is always user-entered → fully volatile
    if is_editable:
        normalised_text = "<USER_INPUT>"
    else:
        normalised_text = normalise_volatile_text(element.get("text"))

    canonical: dict[str, Any] = {
        "cls": cls_name,
        "cd": normalise_volatile_text(element.get("content_description")),
        "txt": normalised_text,
        "bounds": normalise_bounds(element.get("bounds", [0, 0, 0, 0])),
        "click": element.get("clickable", False),
        "edit": is_editable,
        "focus": element.get("focusable", False),
    }
    return canonical


def canonicalise_tree(node: dict[str, Any]) -> dict[str, Any]:
    """Recursively canonicalise the full UI tree."""
    canonical = canonicalise_element(node)
    children = node.get("children", [])
    if children:
        canonical["children"] = [canonicalise_tree(child) for child in children]
    return canonical


def compute_fingerprint(ui_tree: dict[str, Any]) -> str:
    """Compute a deterministic fingerprint from a UI tree.

    Steps:
    1. Canonicalise the tree (normalise volatile values, bucket coords).
    2. Serialize to a deterministic JSON string.
    3. SHA-256 hash → hex string.
    """
    canonical = canonicalise_tree(ui_tree.get("root", ui_tree))
    # Include activity name as a structural discriminator
    activity = ui_tree.get("activity_name", "")
    payload = {
        "activity": activity.split(".")[-1].lower() if activity else "",
        "tree": canonical,
    }
    serialised = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()[:16]


def compute_screen_id(fingerprint: str) -> str:
    """Derive a screen ID from a fingerprint."""
    return f"scr_{fingerprint[:8]}"


# ── Deduplication ────────────────────────────────────────────────────


class ScreenDeduplicator:
    """Tracks seen fingerprints and merges duplicate screens.

    When a new observation arrives:
    1. Canonicalise + fingerprint the tree.
    2. Check if fingerprint is already known.
    3. If known → return existing screen_id (merge).
    4. If new → register and return new screen_id.
    """

    def __init__(self):
        self._fingerprint_to_screen: dict[str, str] = {}
        self._screen_observations: dict[str, int] = {}  # screen_id → observation count
        self.duplicates_merged: int = 0

    def process(self, ui_tree: dict[str, Any]) -> tuple[str, str, bool]:
        """Process a UI tree and return (screen_id, fingerprint, is_new).

        Returns:
        - screen_id: stable logical screen ID
        - fingerprint: canonical fingerprint
        - is_new: True if this is the first time seeing this screen
        """
        fingerprint = compute_fingerprint(ui_tree)
        screen_id = compute_screen_id(fingerprint)

        if fingerprint in self._fingerprint_to_screen:
            # Duplicate — merge
            existing_screen_id = self._fingerprint_to_screen[fingerprint]
            self._screen_observations[existing_screen_id] = (
                self._screen_observations.get(existing_screen_id, 1) + 1
            )
            self.duplicates_merged += 1
            return existing_screen_id, fingerprint, False

        # New screen
        self._fingerprint_to_screen[fingerprint] = screen_id
        self._screen_observations[screen_id] = 1
        return screen_id, fingerprint, True

    def get_known_screens(self) -> dict[str, str]:
        """Return mapping of fingerprint → screen_id."""
        return dict(self._fingerprint_to_screen)

    def get_stats(self) -> dict[str, Any]:
        """Return deduplication statistics."""
        return {
            "unique_screens": len(self._fingerprint_to_screen),
            "duplicates_merged": self.duplicates_merged,
            "screen_observations": dict(self._screen_observations),
        }
