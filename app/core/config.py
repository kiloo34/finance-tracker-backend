from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # SECURITY: no hardcoded default for secret_key — must be set in .env
    database_url: str = "postgresql+asyncpg://root:password@localhost/fintrack"
    secret_key: str = Field(..., description="JWT signing secret — MUST be set in .env")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Load from .env file if it exists
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Instantiate settings to be imported; will raise a ValidationError if SECRET_KEY is missing
settings = Settings()
