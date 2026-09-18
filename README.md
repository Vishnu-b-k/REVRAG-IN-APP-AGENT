# 🤖 RevRag In-App Agent

> Autonomous Android exploration agent that discovers app screens, builds a structured **App Knowledge Pack**, and supports rebuild testing — all without manual flow recording.

**Team:** Vishnu · Maniarasan · Amogh · Slaven  
**Track:** PS-002 · RevRag In-App Agent · AI Build Challenge Bengaluru  
**Date:** 18 September 2026

---

## 🏗️ Architecture

```
┌──────────────┐       POST /ingest-screen        ┌─────────────────────┐
│   Android    │ ──────────────────────────────▶  │  FastAPI Orchestrator │
│  Explorer    │  (screenshot + UI tree)          │                     │
│  (Amogh)     │ ◀──────────────────────────────  │  ┌───────────────┐  │
└──────────────┘   (next_action + elements)       │  │ LLM Provider  │  │
                                                   │  │ (mock/gemini) │  │
                                                   │  └───────┬───────┘  │
                                                   │          │          │
                                                   │  ┌───────▼───────┐  │
                                                   │  │  Exploration  │  │
                                                   │  │ State Machine │  │
                                                   │  └───────┬───────┘  │
                                                   │          │          │
                                                   │  ┌───────▼───────┐  │
                                                   │  │ Design Token │  │
                                                   │  │  Extractor   │  │
                                                   │  └───────┬───────┘  │
                                                   │          │          │
┌──────────────┐   GET /knowledge-pack             │  ┌───────▼───────┐  │
│   Viewer     │ ◀──────────────────────────────  │  │ Knowledge Pack│  │
│ (Maniarasan)  │                                   │  │   Builder     │  │
└──────────────┘                                   │  └───────────────┘  │
                                                   └─────────────────────┘
```

## 📦 Project Structure

```
REVRAG-IN-APP-AGENT/
├── orchestrator/                    # FastAPI backend
│   ├── __init__.py                  # Package + version
│   ├── config.py                    # Environment settings (Pydantic)
│   ├── main.py                      # App entrypoint
│   ├── models/                      # Pydantic schemas (shared contracts)
│   │   ├── observation.py           # Android → Backend request
│   │   ├── action.py                # Backend → Android response
│   │   └── knowledge_pack.py        # Knowledge pack schema (v1.0)
│   ├── providers/                   # LLM provider abstraction
│   │   ├── base.py                  # Abstract interface
│   │   ├── mock.py                  # Deterministic mock (no API key)
│   │   └── gemini.py                # Gemini multimodal provider
│   ├── routes/                      # API endpoints
│   │   ├── health.py                # GET /health
│   │   ├── ingest.py                # POST /ingest-screen
│   │   ├── pack.py                  # GET /knowledge-pack, POST /finalize
│   │   ├── simulate.py              # POST /simulate/run (demo pipeline)
│   │   └── sessions.py              # GET /sessions
│   └── services/                    # Business logic
│       ├── session.py               # Session store + event log
│       ├── screen_ingestion.py      # Ingestion pipeline
│       ├── exploration.py           # Exploration state machine
│       ├── fingerprint.py           # Screen fingerprinting + dedup
│       └── pack_builder.py          # Knowledge pack generation + design tokens
├── design_extractor/                # Design token extraction (Slaven)
│   ├── extractor.py                 # Per-screen: colors, fonts, spacing, layout
│   ├── aggregator.py                # Cross-screen: global design system
│   └── __main__.py                  # CLI entrypoint
├── viewer/                          # Knowledge pack viewer (Maniarsan)
│   ├── src/main.js                  # App logic
│   ├── src/data-loader.js           # Pack loading (file, API, mock)
│   ├── src/style.css                # Styles
│   └── public/screenshots/           # Screen screenshots
├── rebuild_test/                    # Rebuild testing (Amogh)
│   ├── rebuilder.py                 # HTML screen rebuilder from pack
│   ├── compare.py                   # Comparison metrics
│   └── __main__.py                  # CLI entrypoint
├── fixtures/                        # Test data
├── docs/                            # Documentation
├── tests/                           # Pytest suite (125 tests)
├── .env.example                     # Environment template
└── requirements.txt                 # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+**
- **pip**

### 1. Clone & Install

```bash
git clone https://github.com/Vishnu-b-k/REVRAG-IN-APP-AGENT.git
cd REVRAG-IN-APP-AGENT

pip install -r requirements.txt
cp .env.example .env
```

### 2. Run the Server

```bash
python -m orchestrator.main
```

The server starts at **http://localhost:8000** with Swagger docs at **http://localhost:8000/docs**.

### 3. Verify

```bash
curl http://localhost:8000/health
# → {"status":"ok","version":"0.1.0","service":"revrag-orchestrator"}
```

### 4. Run Tests

```bash
pytest tests/ -v
# → 110 passed
```

---

## 🔌 API Endpoints

| Method | Path | Description | Phase |
|--------|------|-------------|-------|
| `GET` | `/health` | Service health check | V-0 |
| `POST` | `/ingest-screen` | Submit observation, get next action | V-1 |
| `GET` | `/knowledge-pack/{session_id}` | Retrieve knowledge pack (may be partial) | V-4 |
| `POST` | `/finalize?session_id=...` | Finalize and compact knowledge pack | V-4 |

### POST /ingest-screen

**Request** (from Android):
```json
{
  "session_id": "abc123",
  "step": 0,
  "screenshot_b64": "<base64 PNG>",
  "ui_tree": {
    "package_name": "com.example.app",
    "activity_name": "com.example.app.LoginActivity",
    "root": {
      "class_name": "android.widget.FrameLayout",
      "bounds": [0, 0, 1080, 2340],
      "children": [...]
    }
  }
}
```

**Response** (to Android):
```json
{
  "screen_id": "scr_58ed9095",
  "state_id": "state_739f7c00302f",
  "is_new_screen": true,
  "description": "User authentication / login screen",
  "elements": [
    {"id": "el_02", "role": "text_input", "label": "Phone number", ...}
  ],
  "candidate_actions": [...],
  "next_action": {
    "type": "type_text",
    "target_element_id": "el_02",
    "value": "9876543210",
    "reason": "Unexplored text_input: Phone number",
    "confidence": 0.9
  }
}
```

### Action Types

| Type | Description |
|------|-------------|
| `tap` | Tap an element |
| `scroll` | Scroll in a direction |
| `type_text` | Enter text in a field |
| `back` | Press Android back button |
| `null` | Exploration complete — stop |

---

## ⚙️ Configuration

All config via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `mock` | Provider: `mock` or `gemini` |
| `LLM_API_KEY` | *(empty)* | Google API key (only for `gemini`) |
| `LLM_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `LLM_TIMEOUT` | `30` | API call timeout (seconds) |
| `LLM_MAX_RETRIES` | `3` | Retry count on failure |
| `MAX_STEP_BUDGET` | `50` | Max exploration steps per session |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `DEBUG` | `true` | Enable hot reload |

### Switching to Gemini

```bash
# In .env:
LLM_PROVIDER=gemini
LLM_API_KEY=your-google-api-key-here
```

If Gemini fails (network error, malformed output), the system **automatically falls back to mock** so Android always gets a valid response.

---

## 🧩 For Team Members

### 📱 Android Team (Amogh)

Your integration point is `POST /ingest-screen`. Serialize the accessibility tree as:

```python
# UIElement fields:
{
    "class_name": "android.widget.EditText",
    "text": "user input here",
    "content_description": "Phone number",
    "bounds": [left, top, right, bottom],
    "clickable": true,
    "editable": true,
    "focusable": true,
    "children": []
}
```

The response tells you exactly what to do next: `type_text`, `tap`, `scroll`, `back`, or `null` (stop).

### 🎨 Viewer Team (Maniarasan)

Your data source is `GET /knowledge-pack/{session_id}` or the sample at `docs/sample_knowledge_pack.json`.

The pack contains:
- **screens**: id, purpose, elements, forms, design_tokens
- **transitions**: from → to with action details
- **journeys**: ordered screen sequences
- **scan_metadata**: stats about the exploration

### 🎨 Design System (Slaven)

Design tokens are now **automatically extracted** by `design_extractor/` and wired into the knowledge pack.
Each screen gets: `dominant_colors`, `font_styles`, `spacing_pattern`, `mode`, `tone`, `component_types`.
The global design system aggregates these across all screens.

---

## 🏗️ Build Phases

| Phase | Name | Owner | Status | Tests |
|-------|------|-------|--------|-------|
| V-0 | Backend Bootstrap | Vishnu | ✅ Done | 15 |
| V-1 | Screen Ingestion + Mock Provider | Vishnu | ✅ Done | 17 |
| V-2 | Exploration State Machine | Vishnu | ✅ Done | 15 |
| V-3 | Stable Fingerprinting + Dedup | Vishnu | ✅ Done | 26 |
| V-4 | Knowledge Pack + Compaction | Vishnu | ✅ Done | 21 |
| V-5 | Gemini Provider Integration | Vishnu | ✅ Done | 16 |
| S-1 | Design Token Extraction | Slaven | ✅ Done | — |
| S-2 | Global Design System Aggregation | Slaven | ✅ Done | — |
| M-0 | Viewer App | Maniarsan | ✅ Done | — |
| A-0 | Simulate + Rebuild Test | Amogh | ✅ Done | — |
| **V-6** | **Full Integration** | **Vishnu** | **✅ Done** | **15** |
| **Total** | | | | **125** |

---

## 🚀 Demo

Run the full simulation pipeline (no Android device required):

```bash
# Start the server
python -m orchestrator.main

# In another terminal, trigger a simulated exploration
curl -X POST http://localhost:8000/simulate/run | python -m json.tool
```

This simulates a 5-screen Android app exploration (Login → OTP → Dashboard → Profile → KYC) and returns a complete knowledge pack with design tokens.

---

## 📜 License

Hackathon project — AI Build Challenge Bengaluru 2026.
