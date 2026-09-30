from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    with patch("app.api.health.check_db_connection", return_value=True):
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"]["status"] == "ok"


def test_health_degraded_when_db_down():
    with patch("app.api.health.check_db_connection", return_value=False):
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"]["status"] == "error"


def test_health_response_shape():
    with patch("app.api.health.check_db_connection", return_value=True):
        response = client.get("/health")
    body = response.json()
    assert set(body.keys()) == {"status", "database"}
    assert set(body["database"].keys()) >= {"status"}
