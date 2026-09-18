"""
Comparison and demo evidence for screen reconstruction.

Computes coverage metrics between knowledge pack screen data and
the rebuilt HTML output. Does NOT require pixel-level image comparison.

Phase S-4: Reconstruction Evidence
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any


def _extract_text_from_html(html_content: str) -> list[str]:
    """Extract visible text content from HTML."""
    # Remove HTML tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Split into words and filter
    words = [w.strip() for w in text.split() if w.strip()]
    return words


def _extract_element_ids_from_html(html_content: str) -> set[str]:
    """Extract element IDs (el_XX) from rebuilt HTML."""
    return set(re.findall(r'id="(el_\d+)"', html_content))


def compare_screen(screen: dict, rebuilt_html: str) -> dict:
    """Compare a knowledge pack screen entry with its rebuilt HTML.
    
    Args:
        screen: Original screen entry from the knowledge pack.
        rebuilt_html: The generated HTML string.
    
    Returns:
        Comparison metrics dict.
    """
    # --- Element coverage ---
    pack_element_ids = set(el.get("id", "") for el in screen.get("elements", []))
    html_element_ids = _extract_element_ids_from_html(rebuilt_html)

    matched_elements = pack_element_ids & html_element_ids
    element_coverage = len(matched_elements) / len(pack_element_ids) if pack_element_ids else 1.0

    # --- Text coverage ---
    pack_labels = set()
    for el in screen.get("elements", []):
        label = el.get("label", "")
        if label:
            for word in label.split():
                pack_labels.add(word.lower())

    html_words = set(w.lower() for w in _extract_text_from_html(rebuilt_html))
    matched_text = pack_labels & html_words
    text_coverage = len(matched_text) / len(pack_labels) if pack_labels else 1.0

    # --- Form field coverage ---
    pack_forms = set(f.get("id", "") for f in screen.get("forms", []))
    # Check for input elements in HTML
    input_count = len(re.findall(r'<input\b', rebuilt_html))
    select_count = len(re.findall(r'<select\b', rebuilt_html))
    form_coverage = min(1.0, (input_count + select_count) / len(pack_forms)) if pack_forms else 1.0

    # --- Layout correspondence ---
    # Check if grid layout is used when pack elements suggest it
    elements = screen.get("elements", [])
    has_grid_elements = False
    if len(elements) >= 2:
        # Check for elements on the same row (similar Y)
        y_positions = [el.get("bounds", [0, 0, 0, 0])[1] for el in elements]
        for i in range(len(y_positions)):
            for j in range(i + 1, len(y_positions)):
                if abs(y_positions[i] - y_positions[j]) < 40:
                    has_grid_elements = True
                    break

    uses_grid = 'class="grid-row"' in rebuilt_html
    layout_match = 1.0 if (has_grid_elements == uses_grid) or uses_grid else 0.5

    # --- Component type coverage ---
    pack_roles = set(el.get("role", "") for el in elements)
    # Map roles to HTML element types
    role_html_map = {
        "button": r"<button\b",
        "text_input": r"<input\b",
        "image": r'class="el-image"',
        "label": r'class="el-label',
        "checkbox": r'type="checkbox"',
        "radio": r'type="radio"',
        "dropdown": r"<select\b",
    }
    matched_roles = 0
    for role in pack_roles:
        pattern = role_html_map.get(role)
        if pattern and re.search(pattern, rebuilt_html):
            matched_roles += 1
    role_coverage = matched_roles / len(pack_roles) if pack_roles else 1.0

    # --- Overall score ---
    overall = (
        element_coverage * 0.3 +
        text_coverage * 0.3 +
        role_coverage * 0.2 +
        layout_match * 0.1 +
        form_coverage * 0.1
    )

    return {
        "screen_id": screen.get("id", "unknown"),
        "screen_name": screen.get("name", "unknown"),
        "metrics": {
            "element_coverage": round(element_coverage, 3),
            "text_coverage": round(text_coverage, 3),
            "component_type_coverage": round(role_coverage, 3),
            "layout_correspondence": round(layout_match, 3),
            "form_field_coverage": round(form_coverage, 3),
            "overall_score": round(overall, 3),
        },
        "details": {
            "pack_elements": len(pack_element_ids),
            "html_elements": len(html_element_ids),
            "matched_elements": len(matched_elements),
            "missing_elements": sorted(pack_element_ids - html_element_ids),
            "pack_text_tokens": len(pack_labels),
            "matched_text_tokens": len(matched_text),
            "missing_text": sorted(pack_labels - matched_text)[:10],
            "has_grid_layout": has_grid_elements,
            "uses_grid_in_html": uses_grid,
        },
    }


def compare_pack(pack_data: dict, rebuilt_htmls: dict[str, str]) -> dict:
    """Compare all rebuilt screens against the pack.
    
    Args:
        pack_data: Full knowledge pack dict.
        rebuilt_htmls: Dict mapping screen_id → HTML string.
    
    Returns:
        Full comparison report.
    """
    screens = pack_data.get("screens", [])
    comparisons = []

    for screen in screens:
        sid = screen.get("id", "unknown")
        if sid in rebuilt_htmls:
            comp = compare_screen(screen, rebuilt_htmls[sid])
            comparisons.append(comp)

    # Aggregate stats
    if comparisons:
        avg_overall = sum(c["metrics"]["overall_score"] for c in comparisons) / len(comparisons)
        avg_element = sum(c["metrics"]["element_coverage"] for c in comparisons) / len(comparisons)
        avg_text = sum(c["metrics"]["text_coverage"] for c in comparisons) / len(comparisons)
    else:
        avg_overall = avg_element = avg_text = 0.0

    return {
        "summary": {
            "screens_rebuilt": len(comparisons),
            "screens_in_pack": len(screens),
            "average_overall_score": round(avg_overall, 3),
            "average_element_coverage": round(avg_element, 3),
            "average_text_coverage": round(avg_text, 3),
        },
        "per_screen": comparisons,
    }


def generate_demo_artifacts(pack_data: dict, rebuilt_htmls: dict[str, str],
                            output_dir: str) -> list[str]:
    """Generate demo folder with comparison artifacts.
    
    Creates:
      - {screen_id}_pack_entry.json  — the knowledge pack entry
      - {screen_id}_rebuilt.html     — the rebuilt HTML
      - comparison_report.json       — metrics
      - comparison_summary.html      — visual summary page
    
    Args:
        pack_data: Full knowledge pack dict.
        rebuilt_htmls: Dict mapping screen_id → HTML string.
        output_dir: Directory to write artifacts.
    
    Returns:
        List of written file paths.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []

    # Per-screen artifacts
    screens = pack_data.get("screens", [])
    for screen in screens:
        sid = screen.get("id", "unknown")
        if sid not in rebuilt_htmls:
            continue

        # Pack entry JSON
        entry_path = out / f"{sid}_pack_entry.json"
        entry_path.write_text(json.dumps(screen, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(str(entry_path))

        # Rebuilt HTML
        html_path = out / f"{sid}_rebuilt.html"
        html_path.write_text(rebuilt_htmls[sid], encoding="utf-8")
        written.append(str(html_path))

    # Comparison report
    report = compare_pack(pack_data, rebuilt_htmls)
    report_path = out / "comparison_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    written.append(str(report_path))

    # Summary HTML page
    summary_html = _generate_summary_html(report, list(rebuilt_htmls.keys()))
    summary_path = out / "comparison_summary.html"
    summary_path.write_text(summary_html, encoding="utf-8")
    written.append(str(summary_path))

    return written


def _generate_summary_html(report: dict, screen_ids: list[str]) -> str:
    """Generate a visual comparison summary HTML page."""
    summary = report.get("summary", {})
    per_screen = report.get("per_screen", [])

    rows_html = ""
    for comp in per_screen:
        m = comp["metrics"]
        score_color = "#4CAF50" if m["overall_score"] >= 0.8 else "#FF9800" if m["overall_score"] >= 0.6 else "#F44336"
        rows_html += f"""
        <tr>
            <td><a href="{comp['screen_id']}_rebuilt.html">{comp['screen_name']}</a></td>
            <td>{comp['screen_id']}</td>
            <td>{m['element_coverage']:.0%}</td>
            <td>{m['text_coverage']:.0%}</td>
            <td>{m['component_type_coverage']:.0%}</td>
            <td>{m['layout_correspondence']:.0%}</td>
            <td style="color: {score_color}; font-weight: bold">{m['overall_score']:.0%}</td>
        </tr>
        """

    # iframe previews for each rebuilt screen
    previews_html = ""
    for sid in screen_ids:
        previews_html += f"""
        <div class="preview-card">
            <h3>{sid}</h3>
            <iframe src="{sid}_rebuilt.html" width="380" height="680"></iframe>
            <p><a href="{sid}_pack_entry.json">View pack entry</a> · <a href="{sid}_rebuilt.html">Open full page</a></p>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rebuild Comparison Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: #F5F5F5;
            color: #333;
            padding: 32px;
        }}
        h1 {{
            font-size: 28px;
            margin-bottom: 8px;
        }}
        .subtitle {{
            font-size: 14px;
            color: #666;
            margin-bottom: 32px;
        }}
        .summary-cards {{
            display: flex;
            gap: 16px;
            margin-bottom: 32px;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 20px 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            flex: 1;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: 700;
            color: #1976D2;
        }}
        .stat-card .label {{
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 32px;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #F0F0F0;
        }}
        th {{
            background: #FAFAFA;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #666;
        }}
        td a {{
            color: #1976D2;
            text-decoration: none;
        }}
        .previews {{
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
        }}
        .preview-card {{
            background: white;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .preview-card h3 {{
            font-size: 14px;
            margin-bottom: 12px;
            font-family: monospace;
        }}
        .preview-card iframe {{
            border: 1px solid #E0E0E0;
            border-radius: 8px;
        }}
        .preview-card p {{
            margin-top: 8px;
            font-size: 12px;
        }}
        .info-flow {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 32px;
            text-align: center;
        }}
        .info-flow .arrow {{
            font-size: 24px;
            color: #1976D2;
            margin: 0 12px;
        }}
        .info-flow .step {{
            display: inline-block;
            background: #E3F2FD;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <h1>🔁 Rebuild Comparison Report</h1>
    <p class="subtitle">Knowledge pack → Screen reconstruction evidence</p>

    <div class="info-flow">
        <span class="step">📱 Original App</span>
        <span class="arrow">→</span>
        <span class="step">📦 Knowledge Pack</span>
        <span class="arrow">→</span>
        <span class="step">🏗️ Rebuild (no screenshot)</span>
        <span class="arrow">→</span>
        <span class="step">📊 Comparison</span>
    </div>

    <div class="summary-cards">
        <div class="stat-card">
            <div class="value">{summary.get('screens_rebuilt', 0)}/{summary.get('screens_in_pack', 0)}</div>
            <div class="label">Screens Rebuilt</div>
        </div>
        <div class="stat-card">
            <div class="value">{summary.get('average_overall_score', 0):.0%}</div>
            <div class="label">Average Score</div>
        </div>
        <div class="stat-card">
            <div class="value">{summary.get('average_element_coverage', 0):.0%}</div>
            <div class="label">Element Coverage</div>
        </div>
        <div class="stat-card">
            <div class="value">{summary.get('average_text_coverage', 0):.0%}</div>
            <div class="label">Text Coverage</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Screen</th>
                <th>ID</th>
                <th>Elements</th>
                <th>Text</th>
                <th>Components</th>
                <th>Layout</th>
                <th>Overall</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <h2 style="margin-bottom: 16px;">Rebuilt Screen Previews</h2>
    <div class="previews">
        {previews_html}
    </div>
</body>
</html>"""
