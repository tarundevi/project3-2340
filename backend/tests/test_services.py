from app.services.retriever import retrieve_context
from app.services.llm import generate_response


def test_retrieve_context_returns_list():
    result = retrieve_context("How much protein should I eat?")
    assert isinstance(result, list)


def test_retrieve_context_returns_strings():
    result = retrieve_context("vitamin C foods")
    for item in result:
        assert isinstance(item, str)


def test_generate_response_returns_string():
    result = generate_response(
        query="How much protein?",
        context=["Adults need 0.8g per kg of body weight."]
    )
    assert isinstance(result, str)
    assert len(result) > 0
