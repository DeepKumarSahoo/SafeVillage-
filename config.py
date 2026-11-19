"""Runtime settings loaded from environment variables and an optional .env file.

Beginner note: nothing secret should be hard-coded in Python files.
Pydantic reads the environment first, then backend/.env. Environment
variables win over the file, which is how tests stay isolated.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SafeVillage"
    environment: str = "development"
    debug: bool = False
    auto_create_tables: bool = True
    seed_demo_data: bool = True

    secret_key: str = "change-me-before-any-real-deployment"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = f"sqlite:///{(BACKEND_DIR / 'safevillage.db').as_posix()}"
    cors_origins: str = "http://127.0.0.1:8000,http://localhost:8000"

    demo_admin_email: str = "admin@safevillage.demo"
    demo_admin_password: str = "Admin@12345"
    demo_citizen_email: str = "citizen@safevillage.demo"
    demo_citizen_password: str = "Citizen@123"

    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"

    maps_provider: str = "google"
    maps_api_key: str = ""

    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def ai_configured(self) -> bool:
        return bool(self.ai_api_key.strip())

    @property
    def maps_configured(self) -> bool:
        return bool(self.maps_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_startup_settings(settings: Settings) -> None:
    """Refuse an obviously unsafe production configuration."""
    if settings.environment.lower() != "production":
        return
    if settings.secret_key.startswith("change-me") or len(settings.secret_key) < 32:
        raise RuntimeError("Set a SECRET_KEY of at least 32 characters before production use.")
    if settings.seed_demo_data:
        raise RuntimeError("Set SEED_DEMO_DATA=false in production. Demo accounts must not be public.")
    if settings.database_url.startswith("sqlite"):
        raise RuntimeError("Use a PostgreSQL DATABASE_URL in production. SQLite is for local demos.")
