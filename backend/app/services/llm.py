import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are NutriBot, a knowledgeable nutritionist assistant. "
    "Answer questions about nutrition, diet, and healthy eating based on the "
    "provided context. If the context doesn't contain relevant information, "
    "use your general nutrition knowledge but note that the information is general advice. "
    "Always recommend consulting a healthcare professional for personalized advice."
)

STUB_RESPONSE = (
    "I'm NutriBot, your nutrition assistant. I'm currently running in demo mode "
    "because the Gemini API key is not configured. Once connected, I'll be able to provide "
    "detailed, evidence-based nutrition advice. Please set your GEMINI_API_KEY "
    "to enable full functionality."
)


def generate_response(query: str, context: list[str]) -> str:
    from app.config import settings

    if not settings.gemini_api_key:
        logger.warning("Gemini API key not configured, returning stub response")
        return STUB_RESPONSE

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            model_name=settings.gemini_model_id,
            system_instruction=SYSTEM_PROMPT,
        )

        context_text = "\n\n".join(context) if context else "No specific context available."

        prompt = (
            f"Context:\n{context_text}\n\n"
            f"Question: {query}\n\n"
            "Please answer the question based on the context provided."
        )

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini call failed: {e}")
        return STUB_RESPONSE
