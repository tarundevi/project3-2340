from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import AuthCredentials, AuthResponse, AuthUser
from app.services.auth import AuthError, get_current_user, signin_user, signup_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(credentials: AuthCredentials):
    try:
        return signup_user(credentials.email, credentials.password, role_key=credentials.role_key)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/signin", response_model=AuthResponse)
def signin(credentials: AuthCredentials):
    try:
        return signin_user(credentials.email, credentials.password, role_key=credentials.role_key)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=AuthUser)
def me(current_user: dict = Depends(get_current_user)):
    return current_user
