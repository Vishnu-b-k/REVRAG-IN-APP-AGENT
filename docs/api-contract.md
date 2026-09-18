# API Contract — RevRag In-App Agent

## POST /ingest-screen

Android sends an observation; the backend returns screen understanding + next action.

### Request

```json
{
  "session_id": "abc123",
  "step": 4,
  "screenshot_b64": "...",
  "ui_tree": {
    "package_name": "com.revrag.targetapp",
    "activity_name": "com.revrag.targetapp.LoginActivity",
    "root": { "class_name": "...", "bounds": [...], "children": [...] }
  },
  "previous_state_id": "state_03"
}
```

### Response

```json
{
  "screen_id": "scr_04",
  "state_id": "state_07",
  "is_new_screen": true,
  "description": "KYC form with name, date and account type fields",
  "elements": [
    {
      "id": "el_12",
      "role": "text_input",
      "label": "Full name",
      "bounds": [x, y, w, h],
      "actions": ["type_text"]
    }
  ],
  "candidate_actions": [...],
  "next_action": {
    "type": "type_text",
    "target_element_id": "el_12",
    "value": "Test User",
    "reason": "Unexplored required field",
    "confidence": 0.91
  }
}
```

## Action Types

| Type | Description | Validator checks |
|------|-------------|-----------------|
| `tap` | Tap an element | target exists, is visible, is clickable |
| `scroll` | Scroll in a direction | target is scrollable |
| `type_text` | Enter text in a field | target is editable, value is test data |
| `back` | Press Android back | always valid |
| `null` | Exploration complete | no target needed |

## Knowledge Pack Schema (v1.0)

```json
{
  "schema_version": "1.0",
  "app_metadata": {},
  "screens": [...],
  "transitions": [...],
  "journeys": [...],
  "global_design_system": {},
  "scan_metadata": {}
}
```

See `orchestrator/models/knowledge_pack.py` for the full Pydantic schema definition.
