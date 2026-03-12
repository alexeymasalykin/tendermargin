from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://tendermargin:changeme@localhost:5432/tendermargin"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    openrouter_api_key: str = ""
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 200


settings = Settings()
