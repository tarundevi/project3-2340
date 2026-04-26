from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import init_auth_db
from app.services.persistence import init_persistence

client = TestClient(app)


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
    return {"Authorization": f"Bearer {signup_response.json()['access_token']}"}


def test_profile_round_trip(monkeypatch, tmp_path):
    configure_local_databases(monkeypatch, tmp_path)
    headers = auth_headers("profile@example.com")

    update_response = client.put(
        "/api/profile",
        json={
            "raw_text": "I have celiac disease, a peanut allergy, and I want to increase protein while keeping sodium low."
        },
        headers=headers,
    )

    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["raw_text"].startswith("I have celiac disease")
    assert payload["summary"]

    get_response = client.get("/api/profile", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["summary"] == payload["summary"]


def test_chat_uses_saved_profile(monkeypatch, tmp_path):
    configure_local_databases(monkeypatch, tmp_path)
    headers = auth_headers("profile-chat@example.com")

    import app.routers.chat as chat_router

    captured = {}
    chat_router.retrieve_context = lambda message, topic="": {"context": ["Context"], "sources": []}

    def fake_generate_response(message, context, topic="", profile=None):
      captured["profile"] = profile
      return "Profile-aware reply"

    chat_router.generate_response = fake_generate_response

    client.put(
        "/api/profile",
        json={"raw_text": "I have diabetes and a shellfish allergy. My goal is weight loss."},
        headers=headers,
    )

    response = client.post(
        "/api/chat",
        json={"message": "What should I eat for dinner?", "topic": "weight_management"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Profile-aware reply"
    assert captured["profile"]["raw_text"].startswith("I have diabetes")
    assert captured["profile"]["summary"]
