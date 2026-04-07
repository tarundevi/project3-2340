from app.services.retriever import retrieve_context
from app.services.llm import generate_response


def test_retrieve_context_returns_list():
    result = retrieve_context("How much protein should I eat?")
    assert isinstance(result["context"], list)


def test_retrieve_context_with_topic_returns_list():
    result = retrieve_context("What vitamins are important?", topic="vitamins_minerals")
    assert isinstance(result["context"], list)


def test_retrieve_context_returns_strings():
    result = retrieve_context("vitamin C foods")
    for item in result["context"]:
        assert isinstance(item, str)


def test_generate_response_returns_string():
    result = generate_response(
        query="How much protein?",
        context=["Adults need 0.8g per kg of body weight."]
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_response_with_topic_returns_string():
    result = generate_response(
        query="What should I eat?",
        context=["Carbohydrates provide energy."],
        topic="macronutrients"
    )
    assert isinstance(result, str)
    assert len(result) > 0
