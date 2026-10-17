from pydantic import AliasChoices, Field
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

    # LLM Gateway
    llm_provider: str = Field(
        default="mock",
        validation_alias=AliasChoices("LLM_PROVIDER", "HINT_LLM_PROVIDER", "llm_provider"),
    )
    llm_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai",
        validation_alias=AliasChoices("LLM_BASE_URL", "HINT_LLM_BASE_URL", "llm_base_url"),
    )
    llm_model: str = Field(
        default="gemini-2.5-flash",
        validation_alias=AliasChoices("LLM_MODEL", "HINT_LLM_MODEL", "llm_model"),
    )
    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_API_KEY", "HINT_LLM_API_KEY", "llm_api_key"),
    )
    llm_timeout_seconds: float = Field(
        default=30.0,
        validation_alias=AliasChoices(
            "LLM_TIMEOUT_SECONDS", "HINT_LLM_TIMEOUT_SECONDS", "llm_timeout_seconds"
        ),
    )
    llm_max_retries: int = Field(
        default=1,
        validation_alias=AliasChoices(
            "LLM_MAX_RETRIES", "HINT_LLM_MAX_RETRIES", "llm_max_retries"
        ),
    )
    llm_daily_call_limit_per_child: int = Field(
        default=50,
        validation_alias=AliasChoices(
            "LLM_DAILY_CALL_LIMIT_PER_CHILD",
            "HINT_LLM_DAILY_CALL_LIMIT_PER_CHILD",
            "llm_daily_call_limit_per_child",
        ),
    )
    llm_pricing: dict[str, dict[str, float]] = Field(
        default_factory=lambda: {
            "gemini-2.5-flash": {"input_per_million": 0.075, "output_per_million": 0.30},
            "gemini-1.5-flash": {"input_per_million": 0.075, "output_per_million": 0.30},
            "gemini-1.5-pro": {"input_per_million": 1.25, "output_per_million": 5.00},
            "mock": {"input_per_million": 0.0, "output_per_million": 0.0},
            "default": {"input_per_million": 0.15, "output_per_million": 0.60},
        }
    )

    model_config = SettingsConfigDict(env_file=".env", env_prefix="HINT_", extra="ignore")


settings = Settings()
