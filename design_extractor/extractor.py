"""
Design token extraction from knowledge pack screen data.

Extracts visual design tokens per screen using deterministic analysis of
UI tree metadata and element bounds. No external LLM calls required.

Phase S-1: Practical Design Extraction
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from typing import Any, Optional


# --------------------------------------------------------------------------- #
#  Android class → semantic role mapping
# --------------------------------------------------------------------------- #

_CLASS_ROLE_MAP: dict[str, str] = {
    "android.widget.Button": "button",
    "android.widget.ImageButton": "button",
    "android.widget.FloatingActionButton": "fab",
    "android.widget.TextView": "label",
    "android.widget.EditText": "text_input",
    "android.widget.ImageView": "image",
    "android.widget.CheckBox": "checkbox",
    "android.widget.RadioButton": "radio",
    "android.widget.Switch": "switch",
    "android.widget.ToggleButton": "toggle",
    "android.widget.Spinner": "dropdown",
    "android.widget.SeekBar": "slider",
    "android.widget.ProgressBar": "progress",
    "android.widget.RecyclerView": "list",
    "android.widget.ListView": "list",
    "android.widget.ScrollView": "scroll_container",
    "android.widget.HorizontalScrollView": "scroll_container",
    "android.widget.LinearLayout": "linear_layout",
    "android.widget.RelativeLayout": "relative_layout",
    "android.widget.FrameLayout": "frame_layout",
    "android.widget.ConstraintLayout": "constraint_layout",
    "android.widget.CardView": "card",
    "android.widget.Toolbar": "toolbar",
    "android.widget.TabLayout": "tabs",
    "android.widget.BottomNavigationView": "bottom_nav",
}


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

def _bounds_to_rect(bounds: list[int]) -> dict:
    """Convert [left, top, right, bottom] → {x, y, w, h}."""
    left, top, right, bottom = bounds
    return {"x": left, "y": top, "w": right - left, "h": bottom - top}


def _flatten_ui_tree(node: dict, depth: int = 0) -> list[dict]:
    """Recursively flatten a UI tree node into a list of elements with depth."""
    result = [{"node": node, "depth": depth}]
    for child in node.get("children", []):
        result.extend(_flatten_ui_tree(child, depth + 1))
    return result


def _classify_role(class_name: str) -> str:
    """Map Android class name to a semantic role."""
    if not class_name:
        return "unknown"
    # Exact match first
    if class_name in _CLASS_ROLE_MAP:
        return _CLASS_ROLE_MAP[class_name]
    # Partial match on simple class name
    simple = class_name.rsplit(".", 1)[-1].lower()
    for key, role in _CLASS_ROLE_MAP.items():
        if key.rsplit(".", 1)[-1].lower() in simple:
            return role
    # Layout containers
    if "layout" in simple:
        return "layout"
    return "unknown"


# --------------------------------------------------------------------------- #
#  Spacing analysis
# --------------------------------------------------------------------------- #

def _analyze_spacing(elements: list[dict]) -> dict:
    """Analyze spacing patterns from element bounds.
    
    Returns spacing info: gaps between elements, margins, padding estimates.
    """
    if not elements:
        return {"pattern": "unknown", "common_gaps": [], "margins": {}}

    leaf_rects = []
    for el in elements:
        node = el["node"]
        bounds = node.get("bounds")
        children = node.get("children", [])
        if bounds and len(bounds) == 4 and not children:
            rect = _bounds_to_rect(bounds)
            if rect["w"] > 0 and rect["h"] > 0:
                leaf_rects.append(rect)

    if len(leaf_rects) < 2:
        return {"pattern": "single_element", "common_gaps": [], "margins": {}}

    # Sort by vertical position, then horizontal
    leaf_rects.sort(key=lambda r: (r["y"], r["x"]))

    # Compute vertical gaps between consecutive elements
    v_gaps = []
    for i in range(1, len(leaf_rects)):
        gap = leaf_rects[i]["y"] - (leaf_rects[i - 1]["y"] + leaf_rects[i - 1]["h"])
        if gap > 0:
            v_gaps.append(gap)

    # Compute horizontal gaps between elements on similar Y
    h_gaps = []
    for i in range(len(leaf_rects)):
        for j in range(i + 1, len(leaf_rects)):
            r1, r2 = leaf_rects[i], leaf_rects[j]
            # Same row: overlapping Y ranges
            y_overlap = min(r1["y"] + r1["h"], r2["y"] + r2["h"]) - max(r1["y"], r2["y"])
            if y_overlap > 0:
                gap = r2["x"] - (r1["x"] + r1["w"])
                if gap > 0:
                    h_gaps.append(gap)

    all_gaps = v_gaps + h_gaps
    if not all_gaps:
        return {"pattern": "overlapping", "common_gaps": [], "margins": {}}

    # Find most common gaps (round to nearest 10px for grouping)
    rounded = [round(g / 10) * 10 for g in all_gaps]
    counter = Counter(rounded)
    common = [str(val) + "px" for val, _ in counter.most_common(5)]

    # Detect pattern type
    unique_rounded = set(rounded)
    if len(unique_rounded) <= 2:
        pattern = "uniform"
    elif len(unique_rounded) <= 4:
        pattern = "structured"
    else:
        pattern = "varied"

    # Estimate margins from leftmost/topmost positions
    min_left = min(r["x"] for r in leaf_rects)
    min_top = min(r["y"] for r in leaf_rects)

    return {
        "pattern": pattern,
        "common_gaps": common,
        "vertical_gaps": [str(g) + "px" for g in sorted(set(v_gaps))[:5]],
        "horizontal_gaps": [str(g) + "px" for g in sorted(set(h_gaps))[:5]],
        "margins": {
            "estimated_left": str(min_left) + "px",
            "estimated_top": str(min_top) + "px",
        },
    }


# --------------------------------------------------------------------------- #
#  Layout analysis
# --------------------------------------------------------------------------- #

def _analyze_layout(elements: list[dict], screen_bounds: list[int]) -> dict:
    """Determine layout structure from element positions."""
    if not elements:
        return {"type": "empty", "columns": 1, "alignment": "unknown"}

    leaf_rects = []
    for el in elements:
        node = el["node"]
        bounds = node.get("bounds")
        children = node.get("children", [])
        if bounds and len(bounds) == 4 and not children:
            rect = _bounds_to_rect(bounds)
            if rect["w"] > 0 and rect["h"] > 0:
                leaf_rects.append(rect)

    if not leaf_rects:
        return {"type": "empty", "columns": 1, "alignment": "unknown"}

    screen_w = screen_bounds[2] - screen_bounds[0] if screen_bounds else 1080

    # Detect column count by grouping X positions
    x_positions = sorted(set(r["x"] for r in leaf_rects))
    # Group positions within 50px of each other
    columns = []
    for x in x_positions:
        merged = False
        for col in columns:
            if abs(x - col[-1]) < 50:
                col.append(x)
                merged = True
                break
        if not merged:
            columns.append([x])

    col_count = len(columns)

    # Detect alignment
    center_x = screen_w / 2
    centered_count = sum(1 for r in leaf_rects if abs((r["x"] + r["w"] / 2) - center_x) < 80)
    left_aligned = sum(1 for r in leaf_rects if r["x"] < screen_w * 0.15)

    if centered_count > len(leaf_rects) * 0.6:
        alignment = "center"
    elif left_aligned > len(leaf_rects) * 0.6:
        alignment = "left"
    else:
        alignment = "mixed"

    # Layout type
    if col_count == 1:
        layout_type = "single_column"
    elif col_count == 2:
        layout_type = "two_column_grid"
    else:
        layout_type = "multi_column"

    return {
        "type": layout_type,
        "columns": col_count,
        "alignment": alignment,
        "content_area": {
            "left": str(min(r["x"] for r in leaf_rects)) + "px",
            "top": str(min(r["y"] for r in leaf_rects)) + "px",
            "right": str(max(r["x"] + r["w"] for r in leaf_rects)) + "px",
            "bottom": str(max(r["y"] + r["h"] for r in leaf_rects)) + "px",
        },
    }


# --------------------------------------------------------------------------- #
#  Typography analysis
# --------------------------------------------------------------------------- #

def _analyze_typography(elements: list[dict]) -> list[str]:
    """Infer typography styles from text element dimensions."""
    text_elements = []
    for el in elements:
        node = el["node"]
        class_name = node.get("class_name", "")
        text = node.get("text", "")
        bounds = node.get("bounds")
        if "TextView" in class_name and text and bounds and len(bounds) == 4:
            rect = _bounds_to_rect(bounds)
            text_elements.append({
                "text": text,
                "height": rect["h"],
                "width": rect["w"],
                "depth": el["depth"],
            })

    # Fallback: use pack element bounds for labels when no TextViews found
    if not text_elements:
        for el in elements:
            node = el["node"]
            text = node.get("text", "") or node.get("content_description", "") or ""
            bounds = node.get("bounds")
            if text and bounds and len(bounds) == 4:
                rect = _bounds_to_rect(bounds)
                if rect["h"] > 0:
                    text_elements.append({
                        "text": text,
                        "height": rect["h"],
                        "width": rect["w"],
                        "depth": el.get("depth", 1),
                    })

    if not text_elements:
        return []

    # Sort by height descending to infer hierarchy
    text_elements.sort(key=lambda e: e["height"], reverse=True)

    styles = []
    seen_heights = set()
    for te in text_elements:
        h = te["height"]
        # Round height to nearest 10 for grouping
        rounded_h = round(h / 10) * 10
        if rounded_h in seen_heights:
            continue
        seen_heights.add(rounded_h)

        # Estimate font size: Android density-independent mapping
        # bounds height ≈ font_size * 1.4 (line height)
        est_font = max(10, round(h / 1.4))

        if est_font >= 28:
            role = "heading"
        elif est_font >= 20:
            role = "subheading"
        elif est_font >= 14:
            role = "body"
        else:
            role = "caption"

        styles.append(f"{role}: ~{est_font}sp (h={h}px, e.g. \"{te['text'][:30]}\")")

    return styles[:6]  # Cap at 6 levels


# --------------------------------------------------------------------------- #
#  Component analysis
# --------------------------------------------------------------------------- #

def _analyze_components(elements: list[dict]) -> list[str]:
    """Identify component types present on screen."""
    roles = set()
    for el in elements:
        node = el["node"]
        class_name = node.get("class_name", "")
        role = _classify_role(class_name)
        if role not in ("unknown", "layout", "frame_layout", "linear_layout",
                        "relative_layout", "constraint_layout"):
            roles.add(role)

    # Also check element-level roles from the pack data
    return sorted(roles)


# --------------------------------------------------------------------------- #
#  Mode and tone detection
# --------------------------------------------------------------------------- #

def _detect_mode(elements: list[dict], screen_bounds: list[int]) -> str:
    """Heuristic for light/dark mode based on element arrangement.
    
    Without pixel data, we default to 'light' (most common for form-based apps).
    Could be enhanced with screenshot pixel analysis later.
    """
    # Simple heuristic: if the app package suggests dark theme, or if we had
    # pixel data we'd check. For now, default to 'light'.
    return "light"


def _detect_tone(elements: list[dict], purpose: str) -> str:
    """Infer UI tone from screen purpose and element composition."""
    purpose_lower = purpose.lower() if purpose else ""

    if any(kw in purpose_lower for kw in ["login", "auth", "otp", "verification", "security"]):
        return "professional"
    if any(kw in purpose_lower for kw in ["dashboard", "home", "main"]):
        return "informational"
    if any(kw in purpose_lower for kw in ["profile", "settings", "preferences"]):
        return "utilitarian"
    if any(kw in purpose_lower for kw in ["feed", "social", "chat", "media"]):
        return "casual"
    if any(kw in purpose_lower for kw in ["form", "kyc", "registration"]):
        return "formal"
    return "neutral"


# --------------------------------------------------------------------------- #
#  Default color inference
# --------------------------------------------------------------------------- #

def _infer_colors(elements: list[dict], purpose: str) -> dict:
    """Infer likely color roles based on element types and screen purpose.
    
    Without screenshot pixel analysis, we provide reasonable defaults
    based on Material Design conventions.
    """
    has_button = any(
        _classify_role(el["node"].get("class_name", "")) == "button"
        for el in elements
    )
    has_input = any(
        _classify_role(el["node"].get("class_name", "")) == "text_input"
        for el in elements
    )

    # Material Design inspired defaults
    colors = {
        "dominant_colors": ["#FFFFFF", "#1976D2", "#424242"],
        "background_color": "#FFFFFF",
        "foreground_color": "#212121",
    }

    if has_button:
        colors["dominant_colors"].append("#1976D2")  # Primary blue
    if has_input:
        colors["dominant_colors"].append("#757575")  # Input hint gray

    # De-duplicate
    colors["dominant_colors"] = list(dict.fromkeys(colors["dominant_colors"]))

    return colors


# --------------------------------------------------------------------------- #
#  Main extraction function
# --------------------------------------------------------------------------- #

def extract_design_tokens(screen_data: dict) -> dict:
    """Extract design tokens from a single screen's data.
    
    Args:
        screen_data: A screen entry dict containing at minimum:
            - elements: list of element dicts with bounds
            - purpose: screen purpose string
            - ui_tree (optional): full Android UI tree
            
    Returns:
        A DesignTokens-compatible dict.
    """
    # Get UI tree or build a flat list from elements
    ui_tree = screen_data.get("ui_tree", {})
    root = ui_tree.get("root", {})
    purpose = screen_data.get("purpose", "")

    if root:
        flat_elements = _flatten_ui_tree(root)
        screen_bounds = root.get("bounds", [0, 0, 1080, 2340])
    else:
        # Build from element list
        flat_elements = [
            {"node": {
                "class_name": "",
                "text": el.get("label", ""),
                "bounds": el.get("bounds", [0, 0, 0, 0]),
                "children": [],
            }, "depth": 1}
            for el in screen_data.get("elements", [])
        ]
        screen_bounds = [0, 0, 1080, 2340]

    # Extract all token categories
    spacing = _analyze_spacing(flat_elements)
    layout = _analyze_layout(flat_elements, screen_bounds)
    typography = _analyze_typography(flat_elements)
    components = _analyze_components(flat_elements)
    colors = _infer_colors(flat_elements, purpose)
    mode = _detect_mode(flat_elements, screen_bounds)
    tone = _detect_tone(flat_elements, purpose)

    # Also use pack-level element roles
    pack_components = sorted(set(
        el.get("role", "") for el in screen_data.get("elements", [])
        if el.get("role")
    ))
    all_components = sorted(set(components + pack_components))

    return {
        "dominant_colors": colors["dominant_colors"],
        "background_color": colors["background_color"],
        "foreground_color": colors["foreground_color"],
        "font_styles": typography,
        "spacing_pattern": spacing["pattern"],
        "spacing_details": {
            "common_gaps": spacing.get("common_gaps", []),
            "vertical_gaps": spacing.get("vertical_gaps", []),
            "horizontal_gaps": spacing.get("horizontal_gaps", []),
            "margins": spacing.get("margins", {}),
        },
        "layout": layout,
        "component_types": all_components,
        "mode": mode,
        "tone": tone,
    }


def extract_from_file(input_path: str) -> dict:
    """Extract design tokens from a screen fixture JSON file.
    
    Args:
        input_path: Path to a screen JSON file.
        
    Returns:
        The screen data enriched with extracted design_tokens.
    """
    with open(input_path, "r") as f:
        screen_data = json.load(f)

    tokens = extract_design_tokens(screen_data)
    screen_data["design_tokens"] = tokens
    return screen_data
