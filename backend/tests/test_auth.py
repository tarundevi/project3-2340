from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_signup_returns_token():
    email = f"auth-user-{uuid4().hex}@example.com"
    response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "password123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == email


def test_signin_returns_token_for_existing_user():
    client.post(
        "/api/auth/signup",
        json={"email": "signin-user@example.com", "password": "password123"},
    )

    response = client.post(
        "/api/auth/signin",
        json={"email": "signin-user@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_me_requires_valid_token():
    response = client.get("/api/auth/me")

    assert response.status_code == 401
