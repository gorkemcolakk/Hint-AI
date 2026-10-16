from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama ayarları. Değerler .env dosyasından veya HINT_* ortam değişkenlerinden okunur."""

    service_name: str = "hint-ai-api"
    environment: str = "local"
    database_url: str = "postgresql://hint:hint@db:5432/hint"
    async_database_url: str = "postgresql+asyncpg://hint:hint@db:5432/hint"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "dev-secret-change-me-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    child_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_prefix="HINT_", extra="ignore")


settings = Settings()
