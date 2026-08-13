from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Dispatch Platform API"
    environment: str = "development"

    database_url: str = "postgresql+psycopg://dispatch_user:dispatch_dev_pass@localhost:5432/dispatch_db"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cors_origins: list[str] = ["http://localhost:5173"]

    fcm_credentials: str | None = None

    # Fase 14 — ver instrucciones completas al final de app/services/push_service.py
    fcm_credentials_path: str | None = Field(default=None, validation_alias="FCM_CREDENTIALS")


settings = Settings()
