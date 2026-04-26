import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings


class AuthError(Exception):
    pass


security = HTTPBearer(auto_error=False)
_JWKS_CACHE: dict[str, dict[str, Any]] = {}


def _auth_db_path() -> Path:
    path = Path(settings.auth_db_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent.parent / path
    return path


def _get_conn() -> sqlite3.Connection:
    db_path = _auth_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db() -> None:
    if settings.auth_mode != "local":
        return

    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _hash_password(password: str, salt: bytes | None = None) -> str:
    password_bytes = password.encode("utf-8")
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, 120_000)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_b64, digest_b64 = stored_hash.split("$", 1)
    except ValueError:
        return False

    salt = base64.b64decode(salt_b64.encode())
    expected_digest = base64.b64decode(digest_b64.encode())
    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(computed, expected_digest)


def _local_token_payload(email: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(minutes=settings.auth_jwt_expiry_minutes)
    return {
        "sub": email,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expiry.timestamp()),
        "iss": "nutribot-local",
    }


def _issue_local_token(email: str) -> str:
    payload = _local_token_payload(email)
    return jwt.encode(payload, settings.auth_jwt_secret, algorithm=settings.auth_jwt_algorithm)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def signup_local_user(email: str, password: str) -> dict[str, Any]:
    normalized_email = _normalize_email(email)
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters.")

    created_at = datetime.now(timezone.utc).isoformat()
    password_hash = _hash_password(password)

    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (normalized_email, password_hash, created_at),
            )
            conn.commit()
    except sqlite3.IntegrityError as exc:
        raise AuthError("An account with that email already exists.") from exc

    return {
        "user": {"id": normalized_email, "email": normalized_email},
        "access_token": _issue_local_token(normalized_email),
        "token_type": "bearer",
    }


def signin_local_user(email: str, password: str) -> dict[str, Any]:
    normalized_email = _normalize_email(email)
    with _get_conn() as conn:
        user = conn.execute(
            "SELECT email, password_hash FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()

    if not user or not _verify_password(password, user["password_hash"]):
        raise AuthError("Invalid email or password.")

    return {
        "user": {"id": normalized_email, "email": normalized_email},
        "access_token": _issue_local_token(normalized_email),
        "token_type": "bearer",
    }


def _cognito_client():
    import boto3

    return boto3.client("cognito-idp", region_name=settings.aws_region)


def _cognito_secret_hash(username: str) -> str:
    if not settings.cognito_app_client_secret:
        return ""
    message = f"{username}{settings.cognito_app_client_id}".encode("utf-8")
    key = settings.cognito_app_client_secret.encode("utf-8")
    digest = hmac.new(key, message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def signup_cognito_user(email: str, password: str) -> dict[str, Any]:
    normalized_email = _normalize_email(email)
    client = _cognito_client()
    kwargs: dict[str, Any] = {
        "ClientId": settings.cognito_app_client_id,
        "Username": normalized_email,
        "Password": password,
        "UserAttributes": [{"Name": "email", "Value": normalized_email}],
    }
    secret_hash = _cognito_secret_hash(normalized_email)
    if secret_hash:
        kwargs["SecretHash"] = secret_hash

    try:
        client.sign_up(**kwargs)
        if settings.cognito_user_pool_id:
            client.admin_confirm_sign_up(
                UserPoolId=settings.cognito_user_pool_id,
                Username=normalized_email,
            )
    except Exception as exc:
        raise AuthError(str(exc)) from exc

    # Attempt sign-in immediately so the UI has a token if the pool allows it.
    return signin_cognito_user(normalized_email, password)


def signin_cognito_user(email: str, password: str) -> dict[str, Any]:
    normalized_email = _normalize_email(email)
    client = _cognito_client()
    auth_parameters = {"USERNAME": normalized_email, "PASSWORD": password}
    secret_hash = _cognito_secret_hash(normalized_email)
    if secret_hash:
        auth_parameters["SECRET_HASH"] = secret_hash

    try:
        response = client.initiate_auth(
            ClientId=settings.cognito_app_client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters=auth_parameters,
        )
    except Exception as exc:
        raise AuthError(str(exc)) from exc

    auth_result = response.get("AuthenticationResult", {})
    access_token = auth_result.get("IdToken") or auth_result.get("AccessToken")
    if not access_token:
        raise AuthError("Cognito sign-in did not return an access token.")

    user_info = decode_token(access_token)
    return {
        "user": {"id": user_info["id"], "email": user_info["email"]},
        "access_token": access_token,
        "token_type": "bearer",
    }


def signup_user(email: str, password: str) -> dict[str, Any]:
    if settings.auth_mode == "cognito":
        return signup_cognito_user(email, password)
    return signup_local_user(email, password)


def signin_user(email: str, password: str) -> dict[str, Any]:
    if settings.auth_mode == "cognito":
        return signin_cognito_user(email, password)
    return signin_local_user(email, password)


def _get_jwks(jwks_url: str) -> dict[str, Any]:
    cached = _JWKS_CACHE.get(jwks_url)
    if cached:
        return cached

    response = httpx.get(jwks_url, timeout=10.0)
    response.raise_for_status()
    payload = response.json()
    _JWKS_CACHE[jwks_url] = payload
    return payload


def _decode_local_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.auth_jwt_secret,
            algorithms=[settings.auth_jwt_algorithm],
            issuer="nutribot-local",
        )
    except jwt.InvalidTokenError as exc:
        raise AuthError("Invalid or expired token.") from exc

    email = payload.get("email") or payload.get("sub")
    if not email:
        raise AuthError("Token is missing the user email.")
    return {"id": email, "email": email}


def _decode_cognito_token(token: str) -> dict[str, Any]:
    if not settings.cognito_user_pool_id or not settings.cognito_app_client_id:
        raise AuthError("Cognito is not fully configured.")

    issuer = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}"
    jwks_url = f"{issuer}/.well-known/jwks.json"
    unverified_header = jwt.get_unverified_header(token)
    jwks = _get_jwks(jwks_url)

    signing_key = None
    for key in jwks.get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
            break

    if not signing_key:
        raise AuthError("Unable to find matching Cognito signing key.")

    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"verify_aud": False},
        )
    except jwt.InvalidTokenError as exc:
        raise AuthError("Invalid or expired Cognito token.") from exc

    email = payload.get("email") or payload.get("cognito:username") or payload.get("sub")
    if not email:
        raise AuthError("Token is missing the user identity.")
    return {"id": payload.get("sub") or email, "email": email}


def decode_token(token: str) -> dict[str, Any]:
    if settings.auth_mode == "cognito":
        return _decode_cognito_token(token)
    return _decode_local_token(token)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        return decode_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


def build_guest_password() -> str:
    return secrets.token_urlsafe(12)
