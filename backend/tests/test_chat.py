from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def setup_module():
    import app.routers.chat as chat_router

    chat_router.retrieve_context = lambda message, topic="": {
        "context": [f"Context for {message}"],
        "sources": [{"title": "Test Source", "url": "https://example.com"}],
    }
    chat_router.generate_response = lambda message, context, topic="": f"Answer: {message}"


def auth_headers(email: str = "chat-user@example.com") -> dict[str, str]:
    signup_response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "password123"},
    )
    if signup_response.status_code not in (200, 400):
        raise AssertionError(signup_response.text)

    signin_response = client.post(
        "/api/auth/signin",
        json={"email": email, "password": "password123"},
    )
    token = signin_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_chat_requires_auth():
    response = client.post("/api/chat", json={"message": "How much protein do I need?"})
    assert response.status_code == 401


def test_chat_returns_200():
    response = client.post(
        "/api/chat",
        json={"message": "How much protein do I need?"},
        headers=auth_headers("chat-200@example.com"),
    )
    assert response.status_code == 200


def test_chat_with_topic_returns_200():
    response = client.post(
        "/api/chat",
        json={"message": "What should I eat?", "topic": "macronutrients"},
        headers=auth_headers("chat-topic@example.com"),
    )
    assert response.status_code == 200


def test_chat_without_topic_defaults_to_empty():
    response = client.post(
        "/api/chat",
        json={"message": "How much water should I drink?"},
        headers=auth_headers("chat-default-topic@example.com"),
    )
    data = response.json()
    assert response.status_code == 200
    assert "response" in data


def test_chat_response_has_required_fields():
    response = client.post(
        "/api/chat",
        json={"message": "What foods have vitamin C?"},
        headers=auth_headers("chat-fields@example.com"),
    )
    data = response.json()
    assert "response" in data
    assert "sources" in data
    assert isinstance(data["response"], str)
    assert isinstance(data["sources"], list)


def test_chat_rejects_empty_message():
    response = client.post(
        "/api/chat",
        json={"message": ""},
        headers=auth_headers("chat-empty@example.com"),
    )
    assert response.status_code == 422


def test_chat_rejects_missing_message():
    response = client.post(
        "/api/chat",
        json={},
        headers=auth_headers("chat-missing@example.com"),
    )
    assert response.status_code == 422
