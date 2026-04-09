from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
ENV_FILES = (
    PROJECT_DIR / ".env",
    BACKEND_DIR / ".env",
)


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model_id: str = "gemma-3-27b-it"
    s3_bucket_name: str = "nutribot-docs"
    chroma_persist_dir: str = "./data/chromadb"
    cors_allowed_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=tuple(str(env_file) for env_file in ENV_FILES),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
