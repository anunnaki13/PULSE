"""Pydantic-settings v2 configuration for the PULSE backend.

Reads `.env` (case-sensitive) at process start. Secrets stored as `SecretStr` so
Pydantic redacts them in `repr()` / structured logs (T-03-I-01 mitigation).

The `SQLALCHEMY_DATABASE_URL` property assembles the asyncpg URL from the
individual Postgres fields so the same `.env` can drive psql, alembic, and the
async engine without duplicating the URL.

See RESEARCH.md Pattern 2 and CONTEXT.md "Auth" + "Tech Stack (locked)" sections.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Auth / signing ---------------------------------------------------
    APP_SECRET_KEY: SecretStr = SecretStr("dev-app-secret-replace-me")
    JWT_SECRET_KEY: SecretStr = SecretStr("dev-jwt-secret-replace-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TTL_MIN: int = 60
    JWT_REFRESH_TTL_DAYS: int = 14

    # --- Postgres (DEC-002 identifiers) -----------------------------------
    POSTGRES_HOST: str = "pulse-db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "pulse"
    POSTGRES_USER: str = "pulse"
    POSTGRES_PASSWORD: SecretStr = SecretStr("replace-me")

    # --- Redis -------------------------------------------------------------
    REDIS_URL: str = "redis://pulse-redis:6379/0"

    # --- App ---------------------------------------------------------------
    APP_BASE_URL: str = "https://pulse.tenayan.local"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # --- AI / OpenRouter ---------------------------------------------------
    OPENROUTER_API_KEY: SecretStr = SecretStr("")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_ROUTINE_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_COMPLEX_MODEL: str = "anthropic/claude-sonnet-4"
    OPENROUTER_TIMEOUT_SECONDS: float = 20.0
    AI_MOCK_MODE: bool = True
    AI_MONTHLY_BUDGET_USD: float = 5.0

    # --- First-admin bootstrap (CONTEXT.md "Auth" → first admin via .env) ---
    INITIAL_ADMIN_EMAIL: str = "admin@pulse.local"
    INITIAL_ADMIN_PASSWORD: SecretStr = SecretStr("change-me-on-first-login")

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
