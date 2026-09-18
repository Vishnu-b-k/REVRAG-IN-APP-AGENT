"""
Screen reconstruction from knowledge pack data only.

Generates static HTML/CSS mockups from screen entries in a knowledge pack.
The original screenshot is NEVER used during generation.

Phase S-3: Pack-Only Reconstruction
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------- #
#  Design token → CSS mapping
# --------------------------------------------------------------------------- #

def _tokens_to_css_vars(tokens: dict) -> str:
    """Convert design tokens to CSS custom properties."""
    bg = tokens.get("background_color", "#FFFFFF") or "#FFFFFF"
    fg = tokens.get("foreground_color", "#212121") or "#212121"
    mode = tokens.get("mode", "light") or "light"

    dominant = tokens.get("dominant_colors", [])
    primary = dominant[1] if len(dominant) > 1 else "#1976D2"
    secondary = dominant[2] if len(dominant) > 2 else "#757575"

    return f"""
    :root {{
        --bg-color: {bg};
        --fg-color: {fg};
        --primary-color: {primary};
        --secondary-color: {secondary};
        --font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;
        --border-radius: 8px;
        --input-border: #BDBDBD;
        --input-bg: {'#FFFFFF' if mode == 'light' else '#333333'};
        --button-text: #FFFFFF;
        --shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    """


def _base_css() -> str:
    """Base CSS reset and common styles."""
    return """
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    body {
        font-family: var(--font-family);
        background-color: var(--bg-color);
        color: var(--fg-color);
        width: 360px;
        min-height: 640px;
        margin: 0 auto;
        position: relative;
        overflow-x: hidden;
        border: 1px solid #E0E0E0;
    }
    .screen-container {
        padding: 16px;
        display: flex;
        flex-direction: column;
        min-height: 640px;
    }
    .screen-header {
        text-align: center;
        margin-bottom: 24px;
        padding-top: 16px;
    }
    .screen-header h1 {
        font-size: 20px;
        font-weight: 500;
        color: var(--fg-color);
    }
    .screen-purpose {
        font-size: 12px;
        color: var(--secondary-color);
        text-align: center;
        margin-bottom: 20px;
        font-style: italic;
    }
    """


def _element_css() -> str:
    """CSS for individual element types."""
    return """
    .el-image {
        width: 120px;
        height: 120px;
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        border-radius: 16px;
        margin: 16px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--button-text);
        font-size: 12px;
        text-align: center;
        box-shadow: var(--shadow);
    }
    .el-label {
        font-size: 16px;
        color: var(--fg-color);
        margin: 8px 0;
        text-align: center;
    }
    .el-label.heading {
        font-size: 22px;
        font-weight: 600;
        margin: 16px 0;
    }
    .el-label.caption {
        font-size: 12px;
        color: var(--secondary-color);
    }
    .el-button {
        background-color: var(--primary-color);
        color: var(--button-text);
        border: none;
        padding: 14px 32px;
        border-radius: var(--border-radius);
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        margin: 8px auto;
        display: block;
        min-width: 200px;
        text-align: center;
        box-shadow: var(--shadow);
        transition: opacity 0.2s;
    }
    .el-button:hover {
        opacity: 0.9;
    }
    .el-button.secondary {
        background-color: transparent;
        color: var(--primary-color);
        border: 1px solid var(--primary-color);
        box-shadow: none;
    }
    .el-text-input {
        width: 100%;
        padding: 14px 16px;
        border: 1px solid var(--input-border);
        border-radius: var(--border-radius);
        font-size: 16px;
        margin: 8px 0;
        background: var(--input-bg);
        color: var(--fg-color);
        outline: none;
        transition: border-color 0.2s;
    }
    .el-text-input:focus {
        border-color: var(--primary-color);
    }
    .el-checkbox, .el-radio, .el-switch, .el-toggle {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 8px 0;
        font-size: 14px;
    }
    .el-dropdown {
        width: 100%;
        padding: 14px 16px;
        border: 1px solid var(--input-border);
        border-radius: var(--border-radius);
        font-size: 16px;
        margin: 8px 0;
        background: var(--input-bg);
        appearance: none;
    }
    .grid-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin: 8px 0;
    }
    .grid-row .el-button {
        min-width: unset;
        width: 100%;
    }
    .el-card {
        background: var(--input-bg);
        border-radius: var(--border-radius);
        padding: 16px;
        margin: 8px 0;
        box-shadow: var(--shadow);
    }
    .spacer {
        flex: 1;
    }
    .element-id {
        position: absolute;
        top: 2px;
        right: 4px;
        font-size: 9px;
        color: #999;
        font-family: monospace;
    }
    .el-wrapper {
        position: relative;
    }
    """


# --------------------------------------------------------------------------- #
#  Element → HTML mapping
# --------------------------------------------------------------------------- #

def _render_element(el: dict, index: int, is_secondary: bool = False) -> str:
    """Render a single element to HTML based on its role."""
    role = el.get("role", "unknown")
    label = html.escape(el.get("label", "") or "")
    el_id = el.get("id", f"el_{index:02d}")

    wrapper_start = f'<div class="el-wrapper" id="{el_id}">'
    id_badge = f'<span class="element-id">{el_id}</span>'
    wrapper_end = '</div>'

    if role == "image":
        inner = f'<div class="el-image">{label}</div>'
    elif role == "label":
        # Detect heading vs caption by bounds height or index
        bounds = el.get("bounds", [])
        height = (bounds[3] - bounds[1]) if len(bounds) == 4 else 0
        if height >= 60:
            css_class = "el-label heading"
        elif height <= 40:
            css_class = "el-label caption"
        else:
            css_class = "el-label"
        inner = f'<div class="{css_class}">{label}</div>'
    elif role == "text_input":
        inner = f'<input type="text" class="el-text-input" placeholder="{label}" />'
    elif role == "button":
        sec_class = " secondary" if is_secondary else ""
        inner = f'<button class="el-button{sec_class}">{label}</button>'
    elif role == "checkbox":
        inner = f'<label class="el-checkbox"><input type="checkbox" /> {label}</label>'
    elif role == "radio":
        inner = f'<label class="el-radio"><input type="radio" /> {label}</label>'
    elif role == "switch" or role == "toggle":
        inner = f'<label class="el-switch"><input type="checkbox" /> {label}</label>'
    elif role == "dropdown":
        inner = f'<select class="el-dropdown"><option>{label}</option></select>'
    elif role == "progress":
        inner = f'<progress style="width:100%;margin:8px 0" max="100" value="50"></progress>'
    else:
        inner = f'<div class="el-label">{label}</div>'

    return f'{wrapper_start}{id_badge}{inner}{wrapper_end}'


# --------------------------------------------------------------------------- #
#  Layout analysis for grid detection
# --------------------------------------------------------------------------- #

def _detect_grid_rows(elements: list[dict]) -> list[list[dict]]:
    """Group elements into rows based on Y-position overlap.
    
    Elements sharing similar Y positions are placed in the same row.
    """
    if not elements:
        return []

    # Sort by top Y position
    sorted_els = sorted(elements, key=lambda e: e.get("bounds", [0, 0, 0, 0])[1])

    rows: list[list[dict]] = []
    current_row: list[dict] = [sorted_els[0]]
    current_y = sorted_els[0].get("bounds", [0, 0, 0, 0])[1]

    for el in sorted_els[1:]:
        y = el.get("bounds", [0, 0, 0, 0])[1]
        h = el.get("bounds", [0, 0, 0, 0])[3] - el.get("bounds", [0, 0, 0, 0])[1]
        # Same row if Y positions are within 60% of element height
        threshold = max(40, h * 0.6) if h > 0 else 40
        if abs(y - current_y) < threshold:
            current_row.append(el)
        else:
            rows.append(current_row)
            current_row = [el]
            current_y = y

    if current_row:
        rows.append(current_row)

    return rows


# --------------------------------------------------------------------------- #
#  Main rebuild function
# --------------------------------------------------------------------------- #

def rebuild_screen(screen: dict) -> str:
    """Rebuild a single screen as static HTML/CSS from pack data.
    
    Args:
        screen: A screen entry dict from the knowledge pack.
                Must contain: name, purpose, elements, design_tokens.
                Must NOT require the original screenshot.
    
    Returns:
        Complete HTML string for the rebuilt screen.
    """
    name = html.escape(screen.get("name", "Unknown Screen"))
    purpose = html.escape(screen.get("purpose", ""))
    screen_id = screen.get("id", "unknown")
    tokens = screen.get("design_tokens", {})
    elements = screen.get("elements", [])
    forms = screen.get("forms", [])

    # Build CSS
    css_vars = _tokens_to_css_vars(tokens)
    base = _base_css()
    el_css = _element_css()

    # Build element HTML using layout-aware rendering
    rows = _detect_grid_rows(elements)
    body_html_parts = []

    for row in rows:
        if len(row) == 1:
            # Single element row
            el = row[0]
            idx = elements.index(el) if el in elements else 0
            body_html_parts.append(_render_element(el, idx))
        elif len(row) == 2:
            # Grid row with 2 columns
            html_parts = []
            for el in sorted(row, key=lambda e: e.get("bounds", [0])[0]):
                idx = elements.index(el) if el in elements else 0
                html_parts.append(_render_element(el, idx))
            body_html_parts.append(f'<div class="grid-row">{"".join(html_parts)}</div>')
        else:
            # Multiple elements — render sequentially
            for el in sorted(row, key=lambda e: e.get("bounds", [0])[0]):
                idx = elements.index(el) if el in elements else 0
                body_html_parts.append(_render_element(el, idx))

    elements_html = "\n        ".join(body_html_parts)

    # Metadata comment for traceability
    meta_comment = f"<!-- Rebuilt from knowledge pack: screen_id={screen_id} -->"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} — Rebuilt</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
    {css_vars}
    {base}
    {el_css}
    </style>
</head>
<body>
{meta_comment}
<div class="screen-container">
    <div class="screen-header">
        <h1>{name}</h1>
    </div>
    <div class="screen-purpose">{purpose}</div>
    
    {elements_html}
</div>
</body>
</html>"""


def rebuild_from_pack(pack_data: dict, screen_ids: list[str] | None = None) -> dict[str, str]:
    """Rebuild multiple screens from a knowledge pack.
    
    Args:
        pack_data: Full knowledge pack dict.
        screen_ids: Optional list of screen IDs to rebuild.
                    If None, rebuilds all screens.
    
    Returns:
        Dict mapping screen_id → HTML string.
    """
    screens = pack_data.get("screens", [])
    results: dict[str, str] = {}

    for screen in screens:
        sid = screen.get("id", "unknown")
        if screen_ids and sid not in screen_ids:
            continue
        results[sid] = rebuild_screen(screen)

    return results


def rebuild_to_files(pack_data: dict, output_dir: str,
                     screen_ids: list[str] | None = None) -> list[str]:
    """Rebuild screens and save as HTML files.
    
    Args:
        pack_data: Full knowledge pack dict.
        output_dir: Directory to write HTML files.
        screen_ids: Optional list of screen IDs to rebuild.
    
    Returns:
        List of written file paths.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    rebuilds = rebuild_from_pack(pack_data, screen_ids)
    written = []

    for sid, html_content in rebuilds.items():
        filename = f"{sid}_rebuilt.html"
        filepath = out / filename
        filepath.write_text(html_content, encoding="utf-8")
        written.append(str(filepath))

    return written
