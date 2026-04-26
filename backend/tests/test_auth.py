import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import init_auth_db
from app.services.persistence import init_persistence

client = TestClient(app)


_TEST_DIR = Path(tempfile.mkdtemp(prefix="nutribot-auth-tests-"))
app_state = __import__("app.config", fromlist=["settings"]).settings
app_state.auth_mode = "local"
app_state.auth_db_path = str(_TEST_DIR / "auth.db")
app_state.persistence_mode = "local"
app_state.persistence_db_path = str(_TEST_DIR / "persistence.db")
init_auth_db()
init_persistence()


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


def test_me_returns_user_role():
    response = client.post(
        "/api/auth/signup",
        json={"email": "admin@example.com", "password": "password123", "role_key": "admin"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"


def test_admin_and_developer_routes_require_roles():
    admin_email = f"admin-{uuid4().hex}@example.com"
    dev_email = f"dev-{uuid4().hex}@example.com"
    user_email = f"user-{uuid4().hex}@example.com"

    user_token = client.post(
        "/api/auth/signup",
        json={"email": user_email, "password": "password123"},
    ).json()["access_token"]
    dev_token = client.post(
        "/api/auth/signup",
        json={"email": dev_email, "password": "password123", "role_key": "dev"},
    ).json()["access_token"]
    admin_token = client.post(
        "/api/auth/signup",
        json={"email": admin_email, "password": "password123", "role_key": "admin"},
    ).json()["access_token"]

    user_headers = {"Authorization": f"Bearer {user_token}"}
    dev_headers = {"Authorization": f"Bearer {dev_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    assert client.get("/api/admin/stats", headers=user_headers).status_code == 403
    assert client.get("/api/admin/stats", headers=dev_headers).status_code == 403
    assert client.get("/api/admin/stats", headers=admin_headers).status_code == 200

    assert client.get("/api/developer/collection", headers=user_headers).status_code == 403
    assert client.get("/api/developer/collection", headers=dev_headers).status_code == 200
    assert client.get("/api/developer/collection", headers=admin_headers).status_code == 200


def test_invalid_role_key_is_rejected():
    response = client.post(
        "/api/auth/signup",
        json={"email": "badrole@example.com", "password": "password123", "role_key": "owner"},
    )
    assert response.status_code == 400
