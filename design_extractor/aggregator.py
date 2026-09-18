"""
Cross-screen design system aggregator.

Combines per-screen design tokens into a global design system using
frequency/consensus so one unusual screen doesn't overwrite the whole system.

Phase S-2: Global Design System
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any


def _majority_vote(values: list[str | None]) -> str | None:
    """Return the most common non-None value, or None."""
    filtered = [v for v in values if v is not None]
    if not filtered:
        return None
    counter = Counter(filtered)
    winner, count = counter.most_common(1)[0]
    # Only report if it appears in at least 40% of screens
    if count / len(filtered) >= 0.4:
        return winner
    return filtered[0]  # Fallback to first value


def _merge_color_palettes(screens_tokens: list[dict]) -> list[str]:
    """Merge dominant_colors from all screens with frequency weighting."""
    color_counter: Counter = Counter()
    for tokens in screens_tokens:
        for color in tokens.get("dominant_colors", []):
            color_counter[color] += 1

    if not color_counter:
        return []

    # Sort by frequency, take top 8 colors
    return [color for color, _ in color_counter.most_common(8)]


def _merge_spacing(screens_tokens: list[dict]) -> list[str]:
    """Aggregate common spacing values across screens."""
    gap_counter: Counter = Counter()
    for tokens in screens_tokens:
        details = tokens.get("spacing_details", {})
        for gap in details.get("common_gaps", []):
            gap_counter[gap] += 1
        for gap in details.get("vertical_gaps", []):
            gap_counter[gap] += 1

    if not gap_counter:
        return []

    return [gap for gap, _ in gap_counter.most_common(6)]


def _merge_components(screens_tokens: list[dict]) -> list[str]:
    """Identify recurring component types across screens."""
    component_counter: Counter = Counter()
    for tokens in screens_tokens:
        for comp in tokens.get("component_types", []):
            component_counter[comp] += 1

    if not component_counter:
        return []

    # Only include components that appear on 2+ screens, or all if few screens
    total_screens = len(screens_tokens)
    threshold = 2 if total_screens >= 3 else 1
    return sorted(
        comp for comp, count in component_counter.items()
        if count >= threshold
    )


def _merge_typography(screens_tokens: list[dict]) -> list[str]:
    """Build a typography hierarchy from cross-screen font style data."""
    style_entries: dict[str, list[str]] = {}  # role → list of descriptions

    for tokens in screens_tokens:
        for style in tokens.get("font_styles", []):
            # Extract the role prefix (e.g., "heading", "body")
            if ":" in style:
                role = style.split(":")[0].strip()
            else:
                role = "unknown"

            if role not in style_entries:
                style_entries[role] = []
            style_entries[role].append(style)

    # Order: heading > subheading > body > caption > unknown
    priority = {"heading": 0, "subheading": 1, "body": 2, "caption": 3, "unknown": 4}
    sorted_roles = sorted(style_entries.keys(), key=lambda r: priority.get(r, 99))

    result = []
    for role in sorted_roles:
        entries = style_entries[role]
        # Pick the most common description for this role
        counter = Counter(entries)
        best, _ = counter.most_common(1)[0]
        result.append(best)

    return result[:6]


def aggregate_design_system(screens_tokens: list[dict]) -> dict:
    """Aggregate per-screen design tokens into a global design system.

    Args:
        screens_tokens: List of DesignTokens dicts (one per screen).

    Returns:
        A GlobalDesignSystem-compatible dict.
    """
    if not screens_tokens:
        return {
            "color_palette": [],
            "spacing_values": [],
            "recurring_components": [],
            "typography_hierarchy": [],
            "tone": None,
            "mode": None,
        }

    return {
        "color_palette": _merge_color_palettes(screens_tokens),
        "spacing_values": _merge_spacing(screens_tokens),
        "recurring_components": _merge_components(screens_tokens),
        "typography_hierarchy": _merge_typography(screens_tokens),
        "tone": _majority_vote([t.get("tone") for t in screens_tokens]),
        "mode": _majority_vote([t.get("mode") for t in screens_tokens]),
    }


def enrich_knowledge_pack(pack_data: dict, screens_tokens: list[dict]) -> dict:
    """Enrich a knowledge pack with per-screen tokens and global design system.

    Args:
        pack_data: Full knowledge pack dict.
        screens_tokens: List of extracted design tokens (one per screen,
                        in the same order as pack_data['screens']).

    Returns:
        The pack dict with updated design_tokens per screen and
        a populated global_design_system.
    """
    # Update per-screen tokens
    for i, screen in enumerate(pack_data.get("screens", [])):
        if i < len(screens_tokens):
            screen["design_tokens"] = screens_tokens[i]

    # Aggregate global design system
    pack_data["global_design_system"] = aggregate_design_system(screens_tokens)

    return pack_data
