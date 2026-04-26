import logging
import re

logger = logging.getLogger(__name__)

_CREATIVE_RE = re.compile(
    r"\b(give me|create|suggest|make me|plan|recipe|meal plan|design|"
    r"recommend|help me|ideas|options|alternatives|what should i|"
    r"what can i|how can i|prepare|cook|weekly|daily|routine|schedule|menu)\b",
    re.IGNORECASE,
)
_EXPLANATION_RE = re.compile(
    r"\b(why|how does|how do|explain|what causes|what happens|"
    r"what effect|what impact|reason|mechanism|process|"
    r"difference between|compare|versus|vs\.?|benefit|risk|"
    r"interact|interaction|affect|effect|describe)\b",
    re.IGNORECASE,
)
_FACTUAL_RE = re.compile(
    r"\b(what is|what are|what was|what were|how much|how many|"
    r"is it|is there|are there|does |which|when |where |"
    r"list|name|define|definition|contain|amount|"
    r"calorie|protein|carb|fat|nutrient|vitamin|mineral|safe|"
    r"allowed|permitted|avoid)\b",
    re.IGNORECASE,
)

_INTENT_INSTRUCTIONS: dict[str, str] = {
    "factual": (
        "Answer directly and concisely. State the key fact first, then add brief "
        "supporting detail. Cite the source from the context if it supports your answer."
    ),
    "explanation": (
        "Provide a thorough, step-by-step explanation. Clarify the underlying mechanism, "
        "reason, or process. Use examples where helpful and cite supporting context."
    ),
    "creative": (
        "Generate a practical, actionable response with specific items, quantities, or steps. "
        "Be concrete rather than general. Tailor all suggestions to the user's profile "
        "constraints listed above."
    ),
}


def classify_intent(query: str) -> str:
    scores = {
        "creative": len(_CREATIVE_RE.findall(query)),
        "explanation": len(_EXPLANATION_RE.findall(query)),
        "factual": len(_FACTUAL_RE.findall(query)),
    }
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "factual"

SYSTEM_PROMPT = (
    "You are NutriBot, a knowledgeable nutritionist assistant. "
    "Answer questions about nutrition, diet, and healthy eating based on the "
    "provided context. If the context doesn't contain relevant information, "
    "use your general nutrition knowledge but note that the information is general advice. "
    "Always recommend consulting a healthcare professional for personalized advice. "
    "When a user profile is provided, treat allergies, intolerances, medical conditions, "
    "and dietary goals as hard constraints for your recommendations."
)

STUB_RESPONSE = (
    "I'm NutriBot, your nutrition assistant. I'm currently running in demo mode "
    "because the Gemini API key is not configured. Once connected, I'll be able to provide "
    "detailed, evidence-based nutrition advice. Please set your GEMINI_API_KEY "
    "to enable full functionality."
)


def summarize_profile(raw_text: str) -> list[str]:
    cleaned = " ".join(raw_text.split()).strip()
    if not cleaned:
        return []

    parts = [segment.strip(" ,") for segment in re.split(r"[.\n;]+", cleaned) if segment.strip()]
    conditions = []
    allergies = []
    goals = []
    other = []

    for part in parts:
        lowered = part.lower()
        if any(token in lowered for token in ("allerg", "intoler", "avoid", "cannot eat", "can't eat")):
            allergies.append(part)
        elif any(token in lowered for token in ("goal", "want to", "trying to", "aim", "lose", "gain", "build", "maintain")):
            goals.append(part)
        elif any(token in lowered for token in ("condition", "diabetes", "blood pressure", "cholesterol", "celiac", "ibs", "pregnan", "kidney", "hypertension")):
            conditions.append(part)
        else:
            other.append(part)

    summary = []
    if conditions:
        summary.append(f"Health conditions: {', '.join(conditions[:3])}.")
    if allergies:
        summary.append(f"Allergies or restrictions: {', '.join(allergies[:3])}.")
    if goals:
        summary.append(f"Dietary goals: {', '.join(goals[:3])}.")
    if other:
        summary.append(f"Additional context: {', '.join(other[:2])}.")

    return summary[:4] if summary else [cleaned]


def _profile_block(profile: dict | None) -> str:
    if not profile:
        return ""

    raw_text = (profile.get("raw_text") or "").strip()
    summary = profile.get("summary") or []
    if not raw_text and not summary:
        return ""

    summary_lines = "\n".join(f"- {item}" for item in summary) if summary else "- No structured summary available."
    raw_line = raw_text if raw_text else "None provided."

    return (
        "User profile constraints:\n"
        f"{summary_lines}\n"
        f"Raw profile text: {raw_line}\n"
        "Use this profile to filter recommendations. Do not suggest foods or plans that conflict with allergies, "
        "medical conditions, or stated restrictions. Flag uncertainty and advise clinician follow-up when risk is non-trivial.\n\n"
    )


def generate_ingredient_interaction(ingredient: str, context: list[str], profile: dict | None = None) -> str:
    from app.config import settings

    if not settings.gemini_api_key:
        logger.warning("Gemini API key not configured, returning stub response")
        return STUB_RESPONSE

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model_kwargs = {"model_name": settings.gemini_model_id}
        if not settings.gemini_model_id.startswith("gemma-"):
            model_kwargs["system_instruction"] = SYSTEM_PROMPT
        model = genai.GenerativeModel(**model_kwargs)

        context_text = "\n\n".join(context) if context else "No specific context available."
        profile_block = _profile_block(profile)

        prompt = (
            (f"Instructions:\n{SYSTEM_PROMPT}\n\n" if settings.gemini_model_id.startswith("gemma-") else "")
            + profile_block
            + f"Context from clinical resources:\n{context_text}\n\n"
            + f"The user wants to understand how the ingredient '{ingredient}' interacts with their specific health conditions listed above.\n"
            + "Explain clearly which of their conditions or restrictions are relevant to this ingredient, why it may be restricted or safe, "
            + "and cite the supporting reason from the clinical resources. If no conditions apply, say so plainly."
        )

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini call failed: {e}")
        return STUB_RESPONSE


def generate_response(query: str, context: list[str], topic: str = "", profile: dict | None = None, intent: str = "") -> str:
    from app.config import settings

    if not settings.gemini_api_key:
        logger.warning("Gemini API key not configured, returning stub response")
        return STUB_RESPONSE

    resolved_intent = intent if intent in _INTENT_INSTRUCTIONS else classify_intent(query)
    intent_instruction = _INTENT_INSTRUCTIONS[resolved_intent]
    logger.info(f"Intent: {resolved_intent} | Query: {query[:80]}")

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model_kwargs = {"model_name": settings.gemini_model_id}
        if not settings.gemini_model_id.startswith("gemma-"):
            model_kwargs["system_instruction"] = SYSTEM_PROMPT
        model = genai.GenerativeModel(**model_kwargs)

        context_text = "\n\n".join(context) if context else "No specific context available."
        topic_line = f"Topic focus: {topic}\n\n" if topic else ""
        profile_block = _profile_block(profile)

        prompt = (
            (f"Instructions:\n{SYSTEM_PROMPT}\n\n" if settings.gemini_model_id.startswith("gemma-") else "")
            + f"{topic_line}"
            + profile_block
            + f"Context:\n{context_text}\n\n"
            + f"Question: {query}\n\n"
            + f"Response style: {intent_instruction}"
        )

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini call failed: {e}")
        return STUB_RESPONSE
