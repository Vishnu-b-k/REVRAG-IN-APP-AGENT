# Design Extraction & Rebuild Test — Data Formats

## Overview

Two standalone Python modules for extracting design tokens and rebuilding screens:

- **design_extractor**: Extracts visual design tokens from knowledge pack screen data
- **rebuild_test**: Reconstructs screens as static HTML/CSS from pack data only

---

## Input: Screen Fixture Format

Each screen fixture JSON file contains a single screen entry compatible with the
`Screen` Pydantic model from `orchestrator/models/knowledge_pack.py`, plus an
optional `ui_tree` for deeper analysis.

```json
{
  "id": "scr_login_01",
  "fingerprint": "a1b2c3d4e5f6a7b8",
  "name": "User authentication",
  "purpose": "User authentication / login screen with phone OTP.",
  "screenshot_url": "screenshots/login.png",
  "elements": [
    {
      "id": "el_00",
      "role": "image",
      "label": "App Logo",
      "bounds": [left, top, right, bottom],
      "actions": []
    }
  ],
  "forms": [
    {"id": "el_02", "label": "Phone number", "input_type": "text", "required": true}
  ],
  "design_tokens": {},
  "ui_tree": {
    "package_name": "com.revrag.targetapp",
    "activity_name": "com.revrag.targetapp.LoginActivity",
    "root": { ... }
  }
}
```

### Element Roles

| Role | HTML mapping | Description |
|------|-------------|-------------|
| `image` | `<div class="el-image">` | Placeholder for image content |
| `label` | `<div class="el-label">` | Text label/heading |
| `button` | `<button>` | Tappable button |
| `text_input` | `<input type="text">` | Text entry field |
| `checkbox` | `<input type="checkbox">` | Checkbox input |
| `radio` | `<input type="radio">` | Radio button |
| `switch` | `<input type="checkbox">` | Toggle switch |
| `dropdown` | `<select>` | Dropdown selector |

---

## Output: Design Tokens Format

```json
{
  "dominant_colors": ["#FFFFFF", "#1976D2", "#424242"],
  "background_color": "#FFFFFF",
  "foreground_color": "#212121",
  "font_styles": [
    "heading: ~50sp (h=70px, e.g. \"Welcome to RevRag\")",
    "body: ~18sp (h=25px, e.g. \"Send OTP\")"
  ],
  "spacing_pattern": "structured",
  "spacing_details": {
    "common_gaps": ["70px", "100px"],
    "vertical_gaps": ["50px", "70px"],
    "horizontal_gaps": [],
    "margins": {"estimated_left": "100px", "estimated_top": "200px"}
  },
  "layout": {
    "type": "single_column",
    "columns": 1,
    "alignment": "center"
  },
  "component_types": ["button", "image", "label", "text_input"],
  "mode": "light",
  "tone": "professional"
}
```

---

## Output: Global Design System Format

```json
{
  "color_palette": ["#FFFFFF", "#1976D2", "#424242", "#757575"],
  "spacing_values": ["70px", "100px", "50px"],
  "recurring_components": ["button", "label", "text_input"],
  "typography_hierarchy": [
    "heading: ~50sp",
    "body: ~18sp"
  ],
  "tone": "professional",
  "mode": "light"
}
```

---

## Output: Comparison Report Format

```json
{
  "summary": {
    "screens_rebuilt": 4,
    "screens_in_pack": 4,
    "average_overall_score": 0.95,
    "average_element_coverage": 1.0,
    "average_text_coverage": 0.9
  },
  "per_screen": [
    {
      "screen_id": "scr_login_01",
      "screen_name": "User authentication",
      "metrics": {
        "element_coverage": 1.0,
        "text_coverage": 0.9,
        "component_type_coverage": 1.0,
        "layout_correspondence": 1.0,
        "form_field_coverage": 1.0,
        "overall_score": 0.96
      }
    }
  ]
}
```

---

## CLI Usage

```bash
# Extract tokens from a single screen fixture
python -m design_extractor --input fixtures/screen_login.json --output tokens.json

# Extract + aggregate from a knowledge pack
python -m design_extractor --aggregate --pack docs/sample_knowledge_pack.json --output enriched_pack.json

# Rebuild screens
python -m rebuild_test --input docs/sample_knowledge_pack.json --output-dir output/rebuild/

# Full comparison + demo artifacts
python -m rebuild_test --compare --input docs/sample_knowledge_pack.json --output-dir demo/rebuild/
```
