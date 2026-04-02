from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_returns_200():
    response = client.post("/api/chat", json={"message": "How much protein do I need?"})
    assert response.status_code == 200


def test_chat_response_has_required_fields():
    response = client.post("/api/chat", json={"message": "What foods have vitamin C?"})
    data = response.json()
    assert "response" in data
    assert "sources" in data
    assert isinstance(data["response"], str)
    assert isinstance(data["sources"], list)


def test_chat_rejects_empty_message():
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_rejects_missing_message():
    response = client.post("/api/chat", json={})
    assert response.status_code == 422
