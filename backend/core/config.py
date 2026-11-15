"""Centralized application settings and environment configuration."""

from functools import lru_cache
import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env
load_dotenv()


class Settings(BaseModel):
    """Configuration settings for CareSync AI."""

    app_name: str = "CareSync AI"
    app_version: str = "2.0.0"
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "production"))
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    test_mode: bool = Field(default_factory=lambda: os.getenv("TEST_MODE", "false").lower() == "true")

    port: int = Field(default_factory=lambda: int(os.getenv("PORT", 8000)))

    # External APIs
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    supabase_url: str = Field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_anon_key: str = Field(default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", ""))

    # Email SMTP
    email_sender: str = Field(default_factory=lambda: os.getenv("EMAIL_SENDER", ""))
    email_password: str = Field(default_factory=lambda: os.getenv("EMAIL_PASSWORD", ""))
    smtp_server: str = Field(default_factory=lambda: os.getenv("SMTP_SERVER", "smtp.gmail.com"))
    smtp_port: int = Field(default_factory=lambda: int(os.getenv("SMTP_PORT", 587)))

    # Security & CORS
    max_file_size_bytes: int = 5 * 1024 * 1024  # 5MB
    rate_limit_rpm: int = 30  # Requests per minute on /api/*

    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "https://caresync-ai-frontend-664caw2tx-jaat-f0ae.vercel.app",
    ]
    allowed_origin_regex: str = r"https://caresync-ai-frontend.*\.vercel\.app"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns a singleton instance of application settings.

    Returns:
        Settings: Cached application settings.
    """
    return Settings()
