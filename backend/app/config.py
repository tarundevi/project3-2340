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
    s3_conversation_prefix: str = "conversations"
    chroma_persist_dir: str = "./data/chromadb"
    cors_allowed_origins: str = "http://localhost:5173"
    auth_mode: str = "local"
    auth_db_path: str = "./data/auth.db"
    auth_jwt_secret: str = "change-me-in-production"
    auth_jwt_algorithm: str = "HS256"
    auth_jwt_expiry_minutes: int = 60 * 24
    aws_region: str = "us-east-1"
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_app_client_secret: str = ""
    admin_allowed_emails: str = ""
    developer_allowed_emails: str = ""
    persistence_mode: str = "local"
    persistence_db_path: str = "./data/persistence.db"
    dynamodb_conversations_table: str = "nutribot-conversations"
    dynamodb_messages_table: str = "nutribot-messages"

    model_config = SettingsConfigDict(
        env_file=tuple(str(env_file) for env_file in ENV_FILES),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def admin_emails(self) -> set[str]:
        return {email.strip().lower() for email in self.admin_allowed_emails.split(",") if email.strip()}

    @property
    def developer_emails(self) -> set[str]:
        return {email.strip().lower() for email in self.developer_allowed_emails.split(",") if email.strip()}


settings = Settings()
