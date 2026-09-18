"""Tests for GET /health endpoint."""


def test_health_returns_200(client):
    """Health endpoint should return 200 with status, version, service."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["service"] == "revrag-orchestrator"


def test_health_version_matches_package(client):
    """Version in health response should match orchestrator.__version__."""
    from orchestrator import __version__

    response = client.get("/health")
    assert response.json()["version"] == __version__
