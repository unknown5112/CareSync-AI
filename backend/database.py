import functools
import os
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


@functools.lru_cache(maxsize=8)
def get_supabase_credentials():
    """Cached accessor for Supabase credentials."""
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_ANON_KEY", "")
    return url, key


def get_supabase_client() -> Client:
    """
    Initializes and returns a Supabase client instance.
    Raises ValueError if required credentials are not found in the environment.
    """
    url, key = get_supabase_credentials()
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL or SUPABASE_ANON_KEY environment variable is not set. "
            "Please check your .env configuration."
        )
    return create_client(url, key)


# Lazy-loaded client instance or instantiated on demand
try:
    url, key = get_supabase_credentials()
    supabase: Client = get_supabase_client() if url and key else None
except Exception:
    supabase = None
