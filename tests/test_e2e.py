"""End-to-end integration tests for V-6.

Tests the full pipeline: ingest → explore → fingerprint → design tokens → pack → viewer-ready.
"""

import json
import copy

import pytest

from orchestrator.models.knowledge_pack import KnowledgePack
from orchestrator.services.pack_builder import build_knowledge_pack, finalize_pack, _HAS_DESIGN_EXTRACTOR
from orchestrator.services.session import EventType, SessionState


# ── Test: Simulate endpoint (full pipeline) ─────────────────────────

class TestSimulateEndpoint:
    """POST /simulate/run exercises every phase: V-1→V-5+V-6."""

    def test_simulate_returns_valid_pack(self, client):
        """Simulation should produce a complete, schema-valid pack."""
        response = client.post("/simulate/run")
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"].startswith("sim-")
        assert data["total_steps"] > 0
        assert data["screens_discovered"] > 0

        # Validate the pack portion
        pack = data["knowledge_pack"]
        assert pack["schema_version"] == "1.0"
        assert len(pack["screens"]) > 0
        assert len(pack["transitions"]) > 0

    def test_simulate_screens_have_purpose(self, client):
        """Every screen in the simulated pack should have a purpose."""
        response = client.post("/simulate/run")
        pack = response.json()["knowledge_pack"]
        for screen in pack["screens"]:
            assert screen["purpose"], f"Screen {screen['id']} missing purpose"

    def test_simulate_screens_have_elements(self, client):
        """Most screens should have elements (some may be element-less)."""
        response = client.post("/simulate/run")
        pack = response.json()["knowledge_pack"]
        screens_with_elements = sum(1 for s in pack["screens"] if len(s["elements"]) > 0)
        # At least half the screens should have elements
        assert screens_with_elements >= len(pack["screens"]) // 2, \
            f"Only {screens_with_elements}/{len(pack['screens'])} screens have elements"

    def test_simulate_has_journey(self, client):
        """Simulated pack should have at least one journey."""
        response = client.post("/simulate/run")
        pack = response.json()["knowledge_pack"]
        assert len(pack["journeys"]) >= 1

    def test_simulate_has_scan_metadata(self, client):
        """Pack should have valid scan metadata."""
        response = client.post("/simulate/run")
        pack = response.json()["knowledge_pack"]
        meta = pack["scan_metadata"]
        assert meta["screens_discovered"] > 0
        assert meta["total_steps"] > 0
        assert meta["pack_size_bytes"] > 0

    def test_simulate_pack_validates_as_knowledge_pack(self, client):
        """The pack from simulation should parse into KnowledgePack model."""
        response = client.post("/simulate/run")
        pack_data = response.json()["knowledge_pack"]
        pack = KnowledgePack.model_validate(pack_data)
        assert pack.schema_version == "1.0"
        assert len(pack.screens) > 0


# ── Test: Design token integration ──────────────────────────────────

class TestDesignTokenIntegration:
    """Verify design extractor is wired into the pack builder."""

    def test_design_extractor_available(self):
        """The design_extractor module should be importable."""
        assert _HAS_DESIGN_EXTRACTOR, "design_extractor module not found"

    def test_simulated_screens_have_design_tokens(self, client):
        """Each screen in simulated pack should have design tokens with colors."""
        response = client.post("/simulate/run")
        pack = response.json()["knowledge_pack"]
        for screen in pack["screens"]:
            tokens = screen.get("design_tokens", {})
            assert tokens is not None, f"Screen {screen['id']} missing design_tokens"
            # At least dominant_colors should be populated from purpose inference
            assert len(tokens.get("dominant_colors", [])) > 0, \
                f"Screen {screen['id']} has no dominant_colors"

    def test_simulated_pack_has_global_design_system(self, client):
        """The global design system should be populated (not all empty)."""
        response = client.post("/simulate/run")
        pack = response.json()["knowledge_pack"]
        gds = pack.get("global_design_system", {})
        # At least color_palette should be non-empty from purpose inference
        assert len(gds.get("color_palette", [])) > 0, \
            "Global design system has no color palette"

    def test_design_tokens_have_mode(self, client):
        """Design tokens should detect light/dark mode."""
        response = client.post("/simulate/run")
        pack = response.json()["knowledge_pack"]
        modes = [s["design_tokens"].get("mode") for s in pack["screens"]]
        # At least some screens should have a mode detected
        assert any(m is not None for m in modes), "No screens have mode detected"

    def test_design_tokens_have_tone(self, client):
        """Design tokens should detect tone."""
        response = client.post("/simulate/run")
        pack = response.json()["knowledge_pack"]
        tones = [s["design_tokens"].get("tone") for s in pack["screens"]]
        assert any(t is not None for t in tones), "No screens have tone detected"


# ── Test: Full pipeline flow ─────────────────────────────────────────

class TestFullPipelineFlow:
    """Ingest → Get Pack → Finalize → Verify enrichment."""

    def test_ingest_get_finalize_flow(self, client, sample_observation):
        """Full flow: ingest multiple screens, get partial pack, finalize."""
        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "e2e-full-flow"

        # Step 1: Ingest first screen
        r1 = client.post("/ingest-screen", json=obs)
        assert r1.status_code == 200
        assert r1.json()["is_new_screen"] is True

        # Step 2: Ingest same screen again (should be duplicate)
        obs["step"] = 1
        r2 = client.post("/ingest-screen", json=obs)
        assert r2.status_code == 200

        # Step 3: Get partial pack
        r3 = client.get("/knowledge-pack/e2e-full-flow")
        assert r3.status_code == 200
        partial_pack = r3.json()
        assert partial_pack["schema_version"] == "1.0"
        assert len(partial_pack["screens"]) >= 1

        # Step 4: Finalize
        r4 = client.post("/finalize?session_id=e2e-full-flow")
        assert r4.status_code == 200
        final_pack = r4.json()
        assert final_pack["scan_metadata"]["pack_size_bytes"] > 0

    def test_sessions_list_after_ingest(self, client, sample_observation):
        """Sessions endpoint should list active sessions."""
        obs = copy.deepcopy(sample_observation)
        obs["session_id"] = "e2e-sessions-list"
        client.post("/ingest-screen", json=obs)

        r = client.get("/sessions")
        assert r.status_code == 200
        sessions = r.json()
        assert "e2e-sessions-list" in sessions


# ── Test: Viewer compatibility ───────────────────────────────────────

class TestViewerCompatibility:
    """Pack output must be compatible with Maniarsan's viewer expectations."""

    def test_pack_has_required_viewer_fields(self, client):
        """Viewer expects: screens with id, name, elements, design_tokens."""
        response = client.post("/simulate/run")
        pack = response.json()["knowledge_pack"]

        for screen in pack["screens"]:
            assert "id" in screen
            assert "name" in screen
            assert "elements" in screen
            assert "design_tokens" in screen

        # Transitions should have from/to
        for t in pack["transitions"]:
            assert "from" in t
            assert "to" in t

    def test_pack_json_roundtrip(self, client):
        """Pack should survive JSON serialize → deserialize."""
        response = client.post("/simulate/run")
        pack_data = response.json()["knowledge_pack"]
        json_str = json.dumps(pack_data)
        reparsed = json.loads(json_str)
        assert reparsed["schema_version"] == pack_data["schema_version"]
        assert len(reparsed["screens"]) == len(pack_data["screens"])
