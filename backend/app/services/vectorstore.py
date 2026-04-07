import math
import re

import chromadb

from app.config import settings

COLLECTION_NAME = "nutrition_docs"
EMBEDDING_DIMENSION = 256


class LocalEmbeddingFunction:
    @classmethod
    def build_from_config(cls, config: dict):
        return cls()

    @staticmethod
    def name() -> str:
        return "default"

    @staticmethod
    def is_legacy() -> bool:
        return False

    @staticmethod
    def default_space() -> str:
        return "cosine"

    @staticmethod
    def supported_spaces() -> list[str]:
        return ["cosine", "l2", "ip"]

    def __call__(self, input):
        return [self._embed_text(text) for text in input]

    def embed_documents(self, input):
        return self.__call__(input)

    def embed_query(self, input):
        if isinstance(input, str):
            return self._embed_text(input)
        return [self._embed_text(text) for text in input]

    @staticmethod
    def get_config() -> dict:
        return {
            "name": "default",
            "type": "custom",
            "space": "cosine",
        }

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIMENSION
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return vector

        for token in tokens:
            index = hash(token) % EMBEDDING_DIMENSION
            vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector


def get_client():
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_collection(create: bool = False):
    client = get_client()
    embedding_function = LocalEmbeddingFunction()
    if create:
        return client.get_or_create_collection(
            COLLECTION_NAME,
            embedding_function=embedding_function,
        )
    return client.get_collection(
        COLLECTION_NAME,
        embedding_function=embedding_function,
    )
