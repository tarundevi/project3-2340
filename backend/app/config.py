from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model_id: str = "gemini-2.0-flash"
    s3_bucket_name: str = "nutribot-docs"
    chroma_persist_dir: str = "./data/chromadb"

    class Config:
        env_file = ".env"


settings = Settings()
