"""
Vantage Backend - Core Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Vantage API"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS – set FRONTEND_URL env var in production to your Vercel domain
    frontend_url: str = "http://localhost:3000"

    # Supabase (set via env vars in production)
    supabase_url: str = "https://rgfaadheklseexqyqmai.supabase.co"
    supabase_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJnZmFhZGhla2xzZWV4cXlxbWFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA4MzA2MzEsImV4cCI6MjA4NjQwNjYzMX0.FNo4upPavq3AQzJDbpXXPCUFDdVplOIG76kxglEO8cQ"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
