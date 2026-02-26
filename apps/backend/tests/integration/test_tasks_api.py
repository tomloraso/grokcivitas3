from fastapi.testclient import TestClient

from bootstrap_app.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_then_list_task() -> None:
    create_response = client.post("/api/v1/tasks", json={"title": "Write docs"})
    assert create_response.status_code == 201

    list_response = client.get("/api/v1/tasks")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload) >= 1
    assert any(item["title"] == "Write docs" for item in payload)
