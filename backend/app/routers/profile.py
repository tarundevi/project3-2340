from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import IngredientCheckRequest, IngredientCheckResponse, ProfileRequest, UserProfile
from app.services.auth import get_current_user
from app.services.llm import generate_ingredient_interaction, summarize_profile
from app.services.persistence import get_profile, save_profile
from app.services.retriever import retrieve_context

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=UserProfile)
def fetch_profile(current_user: dict = Depends(get_current_user)):
    return get_profile(current_user["id"])


@router.put("", response_model=UserProfile)
def update_profile(request: ProfileRequest, current_user: dict = Depends(get_current_user)):
    raw_text = request.raw_text.strip()
    summary = summarize_profile(raw_text)
    return save_profile(current_user["id"], raw_text, summary)


@router.post("/ingredient-check", response_model=IngredientCheckResponse)
def check_ingredient(request: IngredientCheckRequest, current_user: dict = Depends(get_current_user)):
    ingredient = request.ingredient.strip()
    if not ingredient:
        raise HTTPException(status_code=422, detail="Ingredient cannot be empty")
    profile = get_profile(current_user["id"])
    query = f"{ingredient} health effects interactions contraindications"
    retrieval = retrieve_context(query)
    response_text = generate_ingredient_interaction(ingredient, retrieval["context"], profile=profile)
    return IngredientCheckResponse(response=response_text, sources=retrieval["sources"])
