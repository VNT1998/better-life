from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_endpoints():
    for endpoint in ["/health", "/api/health", "/api/v1/health"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


def test_readiness_probe_endpoints():
    for endpoint in ["/ready", "/api/ready", "/api/v1/ready"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"


def test_request_id_header_middleware():
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-response-time" in response.headers
