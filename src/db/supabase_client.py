import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseClientManager:
    _instance: Client = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                # Fallback to empty strings so initialization doesn't crash app startup, 
                # but allows the application to prompt the user or load settings.
                url = url or ""
                key = key or ""
            cls._instance = create_client(url, key)
        return cls._instance

def get_db() -> Client:
    return SupabaseClientManager.get_client()
