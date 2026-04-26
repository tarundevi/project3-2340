from fastapi import APIRouter, Depends

from app.models.schemas import ProfileRequest, UserProfile
from app.services.auth import get_current_user
from app.services.llm import summarize_profile
from app.services.persistence import get_profile, save_profile

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=UserProfile)
def fetch_profile(current_user: dict = Depends(get_current_user)):
    return get_profile(current_user["id"])


@router.put("", response_model=UserProfile)
def update_profile(request: ProfileRequest, current_user: dict = Depends(get_current_user)):
    raw_text = request.raw_text.strip()
    summary = summarize_profile(raw_text)
    return save_profile(current_user["id"], raw_text, summary)
