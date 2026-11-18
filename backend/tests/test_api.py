from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_camera_create_starts_disabled():
    response = client.post(
        "/api/v1/cameras",
        json={
            "name": "Test free weights camera",
            "stream_url": "rtsp://127.0.0.1:554/stream",
            "location": "Free weights",
            "enabled": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["enabled"] is False
    assert response.json()["status"] == "disabled"


def test_reject_invalid_stream_scheme():
    response = client.post(
        "/api/v1/cameras",
        json={"name": "Invalid camera", "stream_url": "ftp://host/stream"},
    )
    assert response.status_code == 422


def test_incidents_list_and_dashboard():
    assert client.get("/api/v1/incidents").status_code == 200
    summary = client.get("/api/v1/dashboard/summary")
    assert summary.status_code == 200
    assert "open_incidents" in summary.json()
