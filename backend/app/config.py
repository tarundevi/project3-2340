from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model_id: str = "gemini-2.0-flash"
    s3_bucket_name: str = "nutribot-docs"
    chroma_persist_dir: str = "./data/chromadb"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
