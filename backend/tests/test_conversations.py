from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import init_auth_db
from app.services.persistence import init_persistence

client = TestClient(app)


def setup_module():
    import app.routers.chat as chat_router

    chat_router.retrieve_context = lambda message, topic="": {
        "context": [f"Context for {message}"],
        "sources": [{"title": "Saved Source", "url": "https://example.com/source"}],
    }
    chat_router.generate_response = lambda message, context, topic="": f"Stored reply: {message}"


def configure_local_databases(monkeypatch, tmp_path):
    monkeypatch.setattr("app.config.settings.auth_db_path", str(tmp_path / "auth.db"))
    monkeypatch.setattr("app.config.settings.persistence_db_path", str(tmp_path / "persistence.db"))
    monkeypatch.setattr("app.config.settings.persistence_mode", "local")
    init_auth_db()
    init_persistence()


def auth_headers(email: str) -> dict[str, str]:
    signup_response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "password123"},
    )
    assert signup_response.status_code == 200
    token = signup_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_fetch_conversation(monkeypatch, tmp_path):
    configure_local_databases(monkeypatch, tmp_path)
    headers = auth_headers("conversations@example.com")

    create_response = client.post(
        "/api/conversations",
        json={"title": "Breakfast Plan", "topic": "macronutrients"},
        headers=headers,
    )

    assert create_response.status_code == 200
    conversation = create_response.json()
    assert conversation["title"] == "Breakfast Plan"

    list_response = client.get("/api/conversations", headers=headers)
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["id"] == conversation["id"]

    detail_response = client.get(f"/api/conversations/{conversation['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["messages"] == []


def test_chat_persists_messages_and_restores_history(monkeypatch, tmp_path):
    configure_local_databases(monkeypatch, tmp_path)
    headers = auth_headers("history@example.com")

    chat_response = client.post(
        "/api/chat",
        json={"message": "What should I eat before a workout?", "topic": "sports_nutrition"},
        headers=headers,
    )

    assert chat_response.status_code == 200
    payload = chat_response.json()
    assert payload["conversation_id"]

    detail_response = client.get(f"/api/conversations/{payload['conversation_id']}", headers=headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert [message["role"] for message in detail["messages"]] == ["user", "bot"]
    assert detail["messages"][0]["content"] == "What should I eat before a workout?"
    assert detail["messages"][1]["content"] == "Stored reply: What should I eat before a workout?"

    list_response = client.get("/api/conversations", headers=headers)
    conversation = list_response.json()[0]
    assert conversation["id"] == payload["conversation_id"]
    assert "workout" in conversation["last_message_preview"]


def test_user_cannot_access_other_users_conversation(monkeypatch, tmp_path):
    configure_local_databases(monkeypatch, tmp_path)
    owner_headers = auth_headers("owner@example.com")
    other_headers = auth_headers("other@example.com")

    create_response = client.post(
        "/api/conversations",
        json={"title": "Private Chat"},
        headers=owner_headers,
    )
    conversation_id = create_response.json()["id"]

    detail_response = client.get(f"/api/conversations/{conversation_id}", headers=other_headers)
    assert detail_response.status_code == 404
