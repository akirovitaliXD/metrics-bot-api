"""Global configuration loaded from .env or environment variables."""
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
import os

# Load .env file in project root if present
env_path = Path(__file__).with_suffix("").parent / ".env"
load_dotenv(env_path)


class Settings:
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./db/metrics.db")
    FETCH_INTERVAL: int = int(os.getenv("FETCH_INTERVAL", "300"))  # seconds
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    SUPER_ADMIN_ID: int | None = int(os.getenv("SUPER_ADMIN_ID", "0")) if os.getenv("SUPER_ADMIN_ID") else None
    USER_ACCESS_RAW: str = os.getenv("USER_ACCESS", "")


@lru_cache
def get_settings() -> Settings:
    return Settings() 