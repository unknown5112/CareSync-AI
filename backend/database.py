"""Supabase database client integration with cached singleton connection."""

from typing import Optional
from supabase import Client, create_client
from backend.core.config import get_settings
from backend.core.logging import logger

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Returns a singleton instance of the Supabase client.

    Returns:
        Client: Configured Supabase client.

    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_ANON_KEY are unset.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    settings = get_settings()
    url = settings.supabase_url
    key = settings.supabase_anon_key

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL or SUPABASE_ANON_KEY environment variable is not set. "
            "Please check your environment configuration."
        )

    try:
        _supabase_client = create_client(url, key)
        logger.info("[Database] Supabase client initialized successfully.")
        return _supabase_client
    except Exception as err:
        logger.error(f"[Database] Failed to initialize Supabase client: {err}")
        raise


# Optional lazy initialization for backward compatibility
try:
    _settings = get_settings()
    supabase: Optional[Client] = (
        get_supabase_client() if _settings.supabase_url and _settings.supabase_anon_key else None
    )
except Exception:
    supabase = None
