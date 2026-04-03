import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL", "https://mock.supabase.co")
key: str = os.getenv("SUPABASE_KEY", "mock-key")

# Initialize the Supabase client
supabase: Client = create_client(url, key)
