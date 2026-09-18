"""Shared test fixtures."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from orchestrator.main import app

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def client():
    """Synchronous test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_observation() -> dict:
    """Load the sample observation fixture."""
    path = FIXTURES_DIR / "sample_observation.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)
