import os
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")


def get_supabase_client() -> Client:
    """
    Initializes and returns a Supabase client instance.
    Raises ValueError if required credentials are not found in the environment.
    """
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError(
            "SUPABASE_URL or SUPABASE_ANON_KEY environment variable is not set. "
            "Please check your .env configuration."
        )
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


# Lazy-loaded client instance or instantiated on demand
try:
    supabase: Client = get_supabase_client() if SUPABASE_URL and SUPABASE_ANON_KEY else None
except Exception:
    supabase = None
